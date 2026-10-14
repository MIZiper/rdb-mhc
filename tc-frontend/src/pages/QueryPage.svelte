<script lang="ts">
    import {
        Button,
        Col,
        Container,
        Input,
        ListGroup,
        Row,
        Spinner,
    } from "@sveltestrap/sveltestrap";
    import { getContext, onMount } from "svelte";
    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import ResourceItem from "../lib/ResourceItem.svelte";
    import type { ItemMeta } from "../schema";
    import { fetch_tags_info, construct_tags_by_ids } from "./FetchMetaHubTags";
    import {
        fetchFieldKeys,
        fetchTypes,
        queryNodes,
        type FieldKey,
        type TypeDescriptor,
    } from "../lib/api";

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
            const cache = await fetch_tags_info(metahub_host, uniqueTagIds);

            items = data.items.map((e: any) => ({
                id: e.id,
                title: e.title,
                description: e.description,
                update_time: new Date(e.updated_at),
                tags: construct_tags_by_ids(e.tag_ids, cache),
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
    <h4>Cross-type Query</h4>

    <Row class="g-2 mb-2">
        <Col md="6">
            <Input
                type="search"
                placeholder="Full-text (title, description, content)"
                bind:value={text}
                onkeypress={(e) => e.key === "Enter" && run()}
            />
        </Col>
        <Col md="3">
            <select class="form-select" bind:value={status}>
                <option value="">Any status</option>
                <option value="draft">Draft</option>
                <option value="pending_review">In Review</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
            </select>
        </Col>
        <Col md="3">
            <Button color="primary" onclick={() => run()}>Search</Button>
        </Col>
    </Row>

    <Row class="g-3 mb-2">
        <Col md="4">
            <div class="panel">
                <div class="panel-title">Types</div>
                {#each types as t}
                    <label class="check">
                        <input
                            type="checkbox"
                            checked={selectedTypes[t.type] ?? false}
                            onchange={() => toggleType(t.type)}
                        />
                        {t.display_name} <code>{t.type}</code>
                    </label>
                {/each}
                {#if types.length === 0}
                    <span class="muted">No types registered.</span>
                {/if}
            </div>
        </Col>
        <Col md="4">
            <div class="panel">
                <div class="panel-title">Tags</div>
                <Button size="sm" onclick={() => (tagSelectorOpen = true)}>
                    Edit Tags
                </Button>
                <label class="check mt-2">
                    <input type="checkbox" bind:checked={includeSubTags} />
                    Include sub-tags
                </label>
                <div class="muted">
                    {selectedTags.map((t) => t.name).join(", ") || "none"}
                </div>
            </div>
        </Col>
        <Col md="4">
            <div class="panel">
                <div class="panel-title">
                    Field filters
                    <Button size="sm" color="secondary" onclick={addFilter}>+</Button>
                </div>
                {#each filters as f, i}
                    <div class="filter-row">
                        <select
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
                        <select bind:value={f.op}>
                            {#each opOptions(fieldKeys.find((k) => k.key === f.key)?.kind) as op}
                                <option value={op}>{op}</option>
                            {/each}
                        </select>
                        <input
                            class="form-control"
                            bind:value={f.value}
                            placeholder="value"
                            onkeypress={(e) => e.key === "Enter" && run()}
                        />
                        <button class="x" onclick={() => removeFilter(i)}>×</button>
                    </div>
                {/each}
            </div>
        </Col>
    </Row>

    {#if loading}
        <div class="text-center py-4"><Spinner /></div>
    {:else if error}
        <p class="text-danger">Error: {error}</p>
    {:else if hasSearched}
        <p class="meta">{total} result(s) — page {page} / {totalPages}</p>
        <ListGroup class="mt-2">
            {#each items as item}
                <ResourceItem {item} />
            {/each}
        </ListGroup>
        {#if totalPages > 1}
            <div class="pager">
                <Button size="sm" disabled={page <= 1} onclick={() => goto(page - 1)}>Prev</Button>
                <span>{page} / {totalPages}</span>
                <Button size="sm" disabled={page >= totalPages} onclick={() => goto(page + 1)}>Next</Button>
            </div>
        {/if}
    {/if}
</Container>

<TagsSelector
    isOpen={tagSelectorOpen}
    onSelect={useTags}
    onCancel={() => (tagSelectorOpen = false)}
/>

<style>
    .panel {
        border: 1px solid #e2e2e2;
        border-radius: 6px;
        padding: 10px;
        height: 100%;
        background: #fafafa;
        font-size: 0.9em;
    }
    .panel-title {
        font-weight: 600;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .check {
        display: block;
        cursor: pointer;
    }
    .muted {
        color: #888;
        font-size: 0.85em;
    }
    .filter-row {
        display: flex;
        gap: 4px;
        margin-bottom: 4px;
    }
    .filter-row select,
    .filter-row input {
        font-size: 0.82em;
        padding: 2px 4px;
        min-width: 0;
    }
    .filter-row input {
        flex: 1;
    }
    .x {
        border: none;
        background: none;
        color: #c00;
        cursor: pointer;
    }
    .pager {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 10px;
    }
</style>
