<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardHeader,
        Col,
        Container,
        Input,
        ListGroup,
        Row,
        Spinner,
    } from "@sveltestrap/sveltestrap";
    import { getContext, onMount } from "svelte";
    import { searchParams } from "sv-router";
    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import ResourceItem from "../components/ResourceItem.svelte";
    import Pagination from "../components/Pagination.svelte";
    import type { ItemMeta } from "../types";
    import { fetchTagsInfo, constructTagsById } from "../lib/api/metahub";
    import { fetchFieldKeys, fetchTypes, queryNodes } from "../lib/api";
    import type { FieldKey, TypeDescriptor } from "../types";
    import {
        boolParam,
        canonicalSearch,
        encodeCsv,
        encodeFilters,
        encodeIdCsv,
        parseCsv,
        parseFilters,
        parseIdCsv,
        stringParam,
    } from "../lib/utils/url";

    let router: any = getContext("router");
    let metahub_host = (getContext("mh_host") as string) || "";

    let types: TypeDescriptor[] = $state([]);
    let fieldKeys: FieldKey[] = $state([]);

    let text = $state("");
    let selectedTypes: Record<string, boolean> = $state({});
    let selectedTags: TagMeta[] = $state([]);
    let tagSelectorOpen = $state(false);
    let includeSubTags = $state(true);
    let status = $state("");
    let filters: { key: string; op: string; value: string }[] = $state([]);

    let items: ItemMeta[] = $state([]);
    let total = $state(0);
    let loading = $state(false);
    let error = $state<string | null>(null);
    let hasSearched = $state(false);

    const pageSize = 10;
    let page = $state(1);
    let totalPages = $derived(Math.max(1, Math.ceil(total / pageSize)));

    let ready = $state(false);
    let lastApplied: string | null = null;
    let applyToken = 0;
    let runToken = 0;

    onMount(async () => {
        const [typeList, keys] = await Promise.all([
            fetchTypes(),
            fetchFieldKeys(),
        ]);
        types = typeList;
        fieldKeys = keys;
        ready = true;
    });

    $effect(() => {
        if (!ready) return;
        const raw = searchParams.toString();
        const canonical = canonicalSearch(raw);
        if (canonical === lastApplied) return;
        lastApplied = canonical;
        void applyUrl(raw);
    });

    function opOptions(kind: string | undefined): string[] {
        if (kind === "number") return ["eq", "ne", "gt", "gte", "lt", "lte"];
        if (kind === "text") return ["contains", "eq", "ne"];
        return ["eq", "ne", "contains"];
    }

    function toggleType(t: string) {
        selectedTypes = { ...selectedTypes, [t]: !selectedTypes[t] };
    }

    function addFilter() {
        filters = [
            ...filters,
            { key: fieldKeys[0]?.key ?? "", op: "eq", value: "" },
        ];
    }

    function removeFilter(i: number) {
        filters = filters.filter((_, idx) => idx !== i);
    }

    function useTags(tags: TagMeta[]) {
        selectedTags = tags ?? [];
        tagSelectorOpen = false;
    }

    async function applyUrl(raw: string) {
        const token = ++applyToken;
        runToken += 1;
        loading = false;
        const params = new URLSearchParams(raw);
        const textValue = stringParam(params, "q") ?? "";
        const typeValues = parseCsv(stringParam(params, "types"));
        const tagIds = parseIdCsv(stringParam(params, "tags"));
        const statusValue = stringParam(params, "status") ?? "";
        const tagMode = stringParam(params, "tag_mode");
        const pageValue = Math.max(
            1,
            Number(stringParam(params, "page") ?? "1") || 1,
        );
        const parsedFilters = parseFilters(stringParam(params, "filters"));

        const selected: Record<string, boolean> = {};
        for (const type of typeValues) selected[type] = true;

        const hydratedFilters = parsedFilters.map((filter) => {
            const kind = fieldKeys.find((key) => key.key === filter.key)?.kind;
            const allowed = opOptions(kind);
            return {
                key: filter.key,
                op: allowed.includes(filter.op) ? filter.op : (allowed[0] ?? "eq"),
                value: filter.value,
            };
        });

        text = textValue;
        selectedTypes = selected;
        selectedTags = tagIds.map((id) => ({ id, name: `@${id}` }));
        includeSubTags = tagMode !== "exact";
        status = statusValue;
        filters = hydratedFilters;
        page = pageValue;

        if (tagIds.length > 0) {
            const cache = await fetchTagsInfo(metahub_host, tagIds);
            if (token !== applyToken) return;
            selectedTags = constructTagsById(tagIds, cache);
        }
        if (token !== applyToken) return;

        const hasCondition =
            textValue.trim() !== "" ||
            typeValues.length > 0 ||
            tagIds.length > 0 ||
            statusValue !== "" ||
            parsedFilters.length > 0 ||
            pageValue > 1;
        const shouldRun =
            hasCondition || boolParam(stringParam(params, "run"));

        if (shouldRun) {
            await execute();
        } else {
            hasSearched = false;
            items = [];
            total = 0;
            error = null;
        }
    }

    function buildQueryUrl(): string {
        const params = new URLSearchParams();
        const query = text.trim();
        if (query) params.set("q", query);

        const typeCsv = encodeCsv(
            Object.keys(selectedTypes).filter((key) => selectedTypes[key]),
        );
        if (typeCsv) params.set("types", typeCsv);

        const tagCsv = encodeIdCsv(
            selectedTags
                .map((tag) => tag.id)
                .filter((id): id is number => typeof id === "number"),
        );
        if (tagCsv) {
            params.set("tags", tagCsv);
            if (!includeSubTags) params.set("tag_mode", "exact");
        }

        if (status) params.set("status", status);

        const filterValue = encodeFilters(
            filters.filter((filter) => filter.key && filter.value !== ""),
        );
        if (filterValue) params.set("filters", filterValue);

        if (page > 1) params.set("page", String(page));
        if (params.size === 0) params.set("run", "1");
        return params.toString();
    }

    function syncUrl() {
        const search = buildQueryUrl();
        const canonical = canonicalSearch(search);
        if (canonical === lastApplied) return;
        lastApplied = canonical;
        router.navigate("/query", { search, scrollToTop: false });
    }

    async function execute() {
        const token = ++runToken;
        loading = true;
        error = null;
        hasSearched = true;
        try {
            const activeFilters = filters
                .filter((f) => f.key && f.value !== "")
                .map((f) => {
                    const fk = fieldKeys.find((k) => k.key === f.key);
                    const value =
                        fk?.kind === "number" ? Number(f.value) : f.value;
                    return { key: f.key, op: f.op as any, value };
                });

            const data = await queryNodes({
                text: text.trim() || undefined,
                types: Object.keys(selectedTypes).filter((k) => selectedTypes[k]),
                tag_ids: selectedTags
                    .map((t) => t.id)
                    .filter((x): x is number => typeof x === "number"),
                tag_mode: includeSubTags ? "ancestors" : "exact",
                filters: activeFilters,
                status: status || undefined,
                page,
                page_size: pageSize,
            });

            const uniqueTagIds = [
                ...new Set(data.items.flatMap((it: any) => it.tag_ids)),
            ] as number[];
            const cache = await fetchTagsInfo(metahub_host, uniqueTagIds);
            if (token !== runToken) return;

            items = data.items.map((e: any) => ({
                id: e.id,
                title: e.title,
                description: e.description,
                update_time: new Date(e.updated_at),
                tags: constructTagsById(e.tag_ids, cache),
                data_type: e.data_type,
                creator_name: e.creator_name,
                creator_sub: e.creator_sub,
                status: e.status,
                visibility: e.visibility || "public",
                fields: e.fields || {},
            }));
            total = data.total || 0;
        } catch (e: any) {
            if (token === runToken) error = e.message || "Query failed";
        } finally {
            if (token === runToken) loading = false;
        }
    }

    async function searchNow() {
        page = 1;
        syncUrl();
        await execute();
    }

    async function goto(p: number) {
        if (p < 1 || p > totalPages) return;
        page = p;
        syncUrl();
        await execute();
    }
</script>

<Container class="my-2" fluid>
    <h4 class="mb-3">Cross-type Query</h4>

    <Row class="g-2 mb-3">
        <Col md="6">
            <Input
                type="search"
                placeholder="Full-text (title, description, content)"
                bind:value={text}
                onkeypress={(e) => e.key === "Enter" && searchNow()}
            />
        </Col>
        <Col md="3">
            <Input type="select" bind:value={status}>
                <option value="">Any status</option>
                <option value="draft">Draft</option>
                <option value="pending_review">In Review</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
            </Input>
        </Col>
        <Col md="3">
            <Button color="primary" onclick={searchNow}>Search</Button>
        </Col>
    </Row>

    <Row class="g-3 mb-3">
        <Col md="4">
            <Card class="h-100">
                <CardHeader class="py-2 fw-semibold">Types</CardHeader>
                <CardBody class="pt-2">
                    {#each types as t}
                        <label class="form-check mb-1">
                            <input
                                class="form-check-input"
                                type="checkbox"
                                checked={selectedTypes[t.type] ?? false}
                                onchange={() => toggleType(t.type)}
                            />
                            <span class="form-check-label">
                                {t.display_name} <code>{t.type}</code>
                            </span>
                        </label>
                    {/each}
                    {#if types.length === 0}
                        <span class="small text-muted">No types registered.</span>
                    {/if}
                </CardBody>
            </Card>
        </Col>
        <Col md="4">
            <Card class="h-100">
                <CardHeader class="py-2 fw-semibold">Tags</CardHeader>
                <CardBody class="pt-2">
                    <Button size="sm" onclick={() => (tagSelectorOpen = true)}>
                        Edit Tags
                    </Button>
                    <label class="form-check mt-2">
                        <input
                            class="form-check-input"
                            type="checkbox"
                            bind:checked={includeSubTags}
                        />
                        <span class="form-check-label">Include sub-tags</span>
                    </label>
                    <div class="small text-muted">
                        {selectedTags.map((t) => t.name).join(", ") || "none"}
                    </div>
                </CardBody>
            </Card>
        </Col>
        <Col md="4">
            <Card class="h-100">
                <CardHeader class="py-2 fw-semibold d-flex justify-content-between align-items-center">
                    Field filters
                    <Button size="sm" color="secondary" onclick={addFilter}>+</Button>
                </CardHeader>
                <CardBody class="pt-2">
                    {#each filters as f, i}
                        <div class="filter-row">
                            <select
                                class="form-select form-select-sm"
                                bind:value={f.key}
                                onchange={() => {
                                    const kind = fieldKeys.find(
                                        (k) => k.key === f.key,
                                    )?.kind;
                                    f.op = opOptions(kind)[0];
                                }}
                            >
                                <option value="">field…</option>
                                {#each fieldKeys as fk}
                                    <option value={fk.key}>
                                        {fk.label || fk.key} ({fk.kind})
                                    </option>
                                {/each}
                            </select>
                            <select class="form-select form-select-sm" bind:value={f.op}>
                                {#each opOptions(fieldKeys.find((k) => k.key === f.key)?.kind) as op}
                                    <option value={op}>{op}</option>
                                {/each}
                            </select>
                            <input
                                class="form-control form-control-sm flex-grow-1"
                                bind:value={f.value}
                                placeholder="value"
                                onkeypress={(e) => e.key === "Enter" && searchNow()}
                            />
                            <Button
                                size="sm"
                                color="link"
                                class="text-danger px-1"
                                onclick={() => removeFilter(i)}
                            >×</Button>
                        </div>
                    {/each}
                </CardBody>
            </Card>
        </Col>
    </Row>

    {#if loading}
        <div class="text-center py-4"><Spinner /></div>
    {:else if error}
        <p class="text-danger">Error: {error}</p>
    {:else if hasSearched}
        <p class="text-muted small">{total} result(s) — page {page} / {totalPages}</p>
        <ListGroup class="mt-2 d-flex flex-column gap-2">
            {#each items as item}
                <ResourceItem {item} />
            {/each}
        </ListGroup>
        <Pagination page={page} totalPages={totalPages} onchange={goto} />
    {/if}
</Container>

<TagsSelector
    isOpen={tagSelectorOpen}
    onSelect={useTags}
    onCancel={() => (tagSelectorOpen = false)}
/>

<style>
    .filter-row {
        display: flex;
        gap: 0.25rem;
        margin-bottom: 0.25rem;
    }
    .filter-row select {
        min-width: 0;
    }
</style>
