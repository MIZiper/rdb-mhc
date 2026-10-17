<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardHeader,
        Col,
        Container,
        Input,
        Row,
        Spinner,
        Table,
    } from "@sveltestrap/sveltestrap";
    import { getContext, onMount } from "svelte";
    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import { aggregateNodes, fetchFieldKeys, fetchTypes } from "../lib/api";
    import type { AggregateGroup, FieldKey, TypeDescriptor } from "../types";

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
    <h4 class="mb-3">Cross-type Aggregate</h4>

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
                                onchange={() =>
                                    (selectedTypes = {
                                        ...selectedTypes,
                                        [t.type]: !selectedTypes[t.type],
                                    })}
                            />
                            <span class="form-check-label">{t.display_name}</span>
                        </label>
                    {/each}
                </CardBody>
            </Card>
        </Col>
        <Col md="4">
            <Card class="h-100">
                <CardHeader class="py-2 fw-semibold">Metric</CardHeader>
                <CardBody class="pt-2">
                    <Input type="select" bsSize="sm" bind:value={func}>
                        <option value="count">count</option>
                        <option value="avg">avg</option>
                        <option value="min">min</option>
                        <option value="max">max</option>
                        <option value="sum">sum</option>
                    </Input>
                    <Input type="select" bsSize="sm" class="mt-2" bind:value={metric}>
                        <option value="">(all numeric values)</option>
                        {#each numberKeys as k}
                            <option value={k.key}>{k.label || k.key}</option>
                        {/each}
                    </Input>
                </CardBody>
            </Card>
        </Col>
        <Col md="4">
            <Card class="h-100">
                <CardHeader class="py-2 fw-semibold">Group by</CardHeader>
                <CardBody class="pt-2">
                    {#each groupKeys as k}
                        <label class="form-check mb-1">
                            <input
                                class="form-check-input"
                                type="checkbox"
                                checked={groupBy[k.key] ?? false}
                                onchange={() =>
                                    (groupBy = {
                                        ...groupBy,
                                        [k.key]: !groupBy[k.key],
                                    })}
                            />
                            <span class="form-check-label">{k.label || k.key}</span>
                        </label>
                    {/each}
                    <label class="form-check">
                        <input class="form-check-input" type="checkbox" bind:checked={groupByTag} />
                        <span class="form-check-label">tag</span>
                    </label>
                </CardBody>
            </Card>
        </Col>
    </Row>

    <Row class="g-3 mb-3 align-items-center">
        <Col md="auto">
            <Button size="sm" onclick={() => (tagSelectorOpen = true)}>Filter Tags</Button>
        </Col>
        <Col md="auto">
            <label class="form-check">
                <input class="form-check-input" type="checkbox" bind:checked={includeSubTags} />
                <span class="form-check-label">Include sub-tags</span>
            </label>
        </Col>
        <Col class="small text-muted">
            {selectedTags.map((t) => t.name).join(", ") || "none"}
        </Col>
        <Col md="auto">
            <Button color="primary" size="sm" onclick={run}>Run</Button>
        </Col>
    </Row>

    {#if loading}
        <div class="text-center py-4"><Spinner /></div>
    {:else if error}
        <p class="text-danger">Error: {error}</p>
    {:else if hasRun}
        <p class="text-muted small">{totalNodes} node(s) in scope.</p>
        {#if groups.length === 0}
            <p class="text-muted">No groups produced.</p>
        {:else}
            <Table bordered hover size="sm" responsive class="small align-middle">
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
                            <td class="text-end font-monospace">{fmt(g.value)}</td>
                            <td class="text-end font-monospace">{g.count}</td>
                            <td class="bar-cell">
                                <div class="progress">
                                    <div
                                        class="progress-bar"
                                        role="progressbar"
                                        style="width:{(Math.abs(g.value ?? 0) / maxAbs) * 100}%"
                                        aria-valuenow={Math.abs(g.value ?? 0)}
                                        aria-valuemin="0"
                                        aria-valuemax={maxAbs}
                                    ></div>
                                </div>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </Table>
        {/if}
    {/if}
</Container>

<TagsSelector
    isOpen={tagSelectorOpen}
    onSelect={useTags}
    onCancel={() => (tagSelectorOpen = false)}
/>

<style>
    .bar-cell {
        width: 200px;
    }
    .bar-cell .progress {
        height: 10px;
    }
</style>
