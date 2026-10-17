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
    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import ResourceItem from "../components/ResourceItem.svelte";
    import Pagination from "../components/Pagination.svelte";
    import type { ItemMeta } from "../types";
    import { fetchTagsInfo, constructTagsById } from "../lib/api/metahub";
    import { fetchFieldKeys, fetchTypes, queryNodes } from "../lib/api";
    import type { FieldKey, TypeDescriptor } from "../types";

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

    onMount(async () => {
        types = await fetchTypes();
        fieldKeys = await fetchFieldKeys();
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

    async function run(resetPage = true) {
        if (resetPage) page = 1;
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
            error = e.message || "Query failed";
        } finally {
            loading = false;
        }
    }

    function goto(p: number) {
        if (p < 1 || p > totalPages) return;
        page = p;
        run(false);
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
                onkeypress={(e) => e.key === "Enter" && run()}
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
            <Button color="primary" onclick={() => run()}>Search</Button>
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
                                onkeypress={(e) => e.key === "Enter" && run()}
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
