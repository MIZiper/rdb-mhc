<script lang="ts">
    import {
        Button,
        Col,
        Container,
        Row,
        Spinner,
    } from "@sveltestrap/sveltestrap";
    import { getContext, onMount } from "svelte";
    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import {
        aggregateNodes,
        fetchFieldKeys,
        fetchTypes,
        type AggregateGroup,
        type FieldKey,
        type TypeDescriptor,
    } from "../lib/api";

    let metahub_host = (getContext("mh_host") as string) || "";

    let types: TypeDescriptor[] = $state([]);
    let fieldKeys: FieldKey[] = $state([]);

    let selectedTypes: Record<string, boolean> = $state({});
    let selectedTags: TagMeta[] = $state([]);
    let tagSelectorOpen = $state(false);
    let includeSubTags = $state(true);

    let func: string = $state("avg");
    let metric: string = $state("");
    let groupBy: Record<string, boolean> = $state({});
    let groupByTag = $state(false);

    let groups: AggregateGroup[] = $state([]);
    let totalNodes = $state(0);
    let loading = $state(false);
    let error = $state<string | null>(null);
    let hasRun = $state(false);

    let numberKeys = $derived(fieldKeys.filter((k) => k.kind === "number"));
    let groupKeys = $derived(fieldKeys.filter((k) => k.kind !== "text"));

    let groupColumns = $derived.by(() => {
        const cols = new Set<string>();
        for (const g of groups) {
            for (const k of Object.keys(g.group)) cols.add(k);
        }
        return [...cols];
    });

    let maxAbs = $derived(
        groups.reduce((m, g) => Math.max(m, Math.abs(g.value ?? 0)), 0) || 1,
    );

    onMount(async () => {
        types = await fetchTypes();
        fieldKeys = await fetchFieldKeys();
        const first = numberKeys[0];
        if (first) metric = first.key;
    });

    function useTags(tags: TagMeta[]) {
        selectedTags = tags ?? [];
        tagSelectorOpen = false;
    }

    async function run() {
        loading = true;
        error = null;
        hasRun = true;
        try {
            const data = await aggregateNodes({
                types: Object.keys(selectedTypes).filter((k) => selectedTypes[k]),
                tag_ids: selectedTags
                    .map((t) => t.id)
                    .filter((x): x is number => typeof x === "number"),
                tag_mode: includeSubTags ? "ancestors" : "exact",
                group_by: Object.keys(groupBy).filter((k) => groupBy[k]),
                group_by_tag: groupByTag,
                metric: metric || null,
                func: func as any,
            });
            groups = data.groups;
            totalNodes = data.total_nodes;
        } catch (e: any) {
            error = e.message || "Aggregate failed";
        } finally {
            loading = false;
        }
    }

    function fmt(v: number | null): string {
        if (v === null || v === undefined) return "—";
        return Number.isFinite(v) ? Number(v).toFixed(4).replace(/\.?0+$/, "") : String(v);
    }
</script>

<Container class="my-2" fluid>
    <h4>Cross-type Aggregate</h4>

    <Row class="g-3 mb-2">
        <Col md="4">
            <div class="panel">
                <div class="panel-title">Types</div>
                {#each types as t}
                    <label class="check">
                        <input
                            type="checkbox"
                            checked={selectedTypes[t.type] ?? false}
                            onchange={() =>
                                (selectedTypes = {
                                    ...selectedTypes,
                                    [t.type]: !selectedTypes[t.type],
                                })}
                        />
                        {t.display_name}
                    </label>
                {/each}
            </div>
        </Col>
        <Col md="4">
            <div class="panel">
                <div class="panel-title">Metric</div>
                <select class="form-select form-select-sm" bind:value={func}>
                    <option value="count">count</option>
                    <option value="avg">avg</option>
                    <option value="min">min</option>
                    <option value="max">max</option>
                    <option value="sum">sum</option>
                </select>
                <select class="form-select form-select-sm mt-2" bind:value={metric}>
                    <option value="">(all numeric values)</option>
                    {#each numberKeys as k}
                        <option value={k.key}>{k.label || k.key}</option>
                    {/each}
                </select>
            </div>
        </Col>
        <Col md="4">
            <div class="panel">
                <div class="panel-title">Group by</div>
                {#each groupKeys as k}
                    <label class="check">
                        <input
                            type="checkbox"
                            checked={groupBy[k.key] ?? false}
                            onchange={() =>
                                (groupBy = {
                                    ...groupBy,
                                    [k.key]: !groupBy[k.key],
                                })}
                        />
                        {k.label || k.key}
                    </label>
                {/each}
                <label class="check">
                    <input type="checkbox" bind:checked={groupByTag} />
                    tag
                </label>
            </div>
        </Col>
    </Row>

    <Row class="g-3 mb-3">
        <Col md="4">
            <Button size="sm" onclick={() => (tagSelectorOpen = true)}>Filter Tags</Button>
            <label class="check ms-2">
                <input type="checkbox" bind:checked={includeSubTags} />
                Include sub-tags
            </label>
            <div class="muted">{selectedTags.map((t) => t.name).join(", ") || "none"}</div>
        </Col>
        <Col md="4">
            <Button color="primary" size="sm" onclick={run}>Run</Button>
        </Col>
    </Row>

    {#if loading}
        <div class="text-center py-4"><Spinner /></div>
    {:else if error}
        <p class="text-danger">Error: {error}</p>
    {:else if hasRun}
        <p class="muted">{totalNodes} node(s) in scope.</p>
        {#if groups.length === 0}
            <p class="muted">No groups produced.</p>
        {:else}
            <div class="table-wrap">
                <table class="agg-table">
                    <thead>
                        <tr>
                            {#each groupColumns as c}
                                <th>{c}</th>
                            {/each}
                            <th>{func}{metric ? `(${metric})` : ""}</th>
                            <th>count</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each groups as g}
                            <tr>
                                {#each groupColumns as c}
                                    <td>{g.group[c] ?? "—"}</td>
                                {/each}
                                <td class="mono">{fmt(g.value)}</td>
                                <td class="mono">{g.count}</td>
                                <td class="bar-cell">
                                    <span
                                        class="bar"
                                        style="width:{(Math.abs(g.value ?? 0) / maxAbs) * 100}%"
                                    ></span>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
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
    }
    .check {
        display: block;
        cursor: pointer;
    }
    .muted {
        color: #888;
        font-size: 0.85em;
    }
    .table-wrap {
        overflow-x: auto;
    }
    .agg-table {
        border-collapse: collapse;
        font-size: 0.85em;
        min-width: 60%;
    }
    .agg-table th,
    .agg-table td {
        padding: 3px 10px;
        border: 1px solid #e0e0e0;
        text-align: left;
    }
    .agg-table th {
        background: #f7f7f8;
    }
    .mono {
        font-family: monospace;
        text-align: right;
    }
    .bar-cell {
        width: 200px;
    }
    .bar {
        display: inline-block;
        height: 10px;
        background: #49a9a7;
        border-radius: 2px;
        min-width: 1px;
    }
</style>
