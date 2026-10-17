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
    import { searchParams } from "sv-router";
    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import { aggregateNodes, fetchFieldKeys, fetchTypes } from "../lib/api";
    import { constructTagsById, fetchTagsInfo } from "../lib/api/metahub";
    import type { AggregateGroup, FieldKey, TypeDescriptor } from "../types";
    import {
        boolParam,
        canonicalSearch,
        encodeCsv,
        encodeIdCsv,
        parseCsv,
        parseIdCsv,
        stringParam,
    } from "../lib/utils/url";

    let router: any = getContext("router");
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

    let ready = $state(false);
    let lastApplied: string | null = null;
    let applyToken = 0;
    let runToken = 0;

    let numberKeys = $derived(fieldKeys.filter((k) => k.kind === "number"));
    let groupKeys = $derived(fieldKeys.filter((k) => k.kind !== "text"));

    let fieldTypes = $derived.by(() => {
        const map = new Map<string, string[]>();
        for (const t of types) {
            for (const f of t.fields) {
                const names = map.get(f.key) ?? [];
                if (!names.includes(t.display_name)) {
                    names.push(t.display_name);
                }
                map.set(f.key, names);
            }
        }
        return map;
    });

    function fieldSources(key: string): string {
        return (fieldTypes.get(key) ?? []).join(", ");
    }

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

    function useTags(tags: TagMeta[]) {
        selectedTags = tags ?? [];
        tagSelectorOpen = false;
    }

    async function applyUrl(raw: string) {
        const token = ++applyToken;
        runToken += 1;
        loading = false;
        const params = new URLSearchParams(raw);
        const typeValues = parseCsv(stringParam(params, "types"));
        const tagIds = parseIdCsv(stringParam(params, "tags"));
        const tagMode = stringParam(params, "tag_mode");
        const funcValue = stringParam(params, "func");
        const hasMetric = params.has("metric");
        const groupByValues = parseCsv(stringParam(params, "group_by"));

        const selected: Record<string, boolean> = {};
        for (const type of typeValues) selected[type] = true;

        const groupSelection: Record<string, boolean> = {};
        for (const key of groupByValues) groupSelection[key] = true;

        selectedTypes = selected;
        selectedTags = tagIds.map((id) => ({ id, name: `@${id}` }));
        includeSubTags = tagMode !== "exact";
        func = ["count", "avg", "min", "max", "sum"].includes(funcValue ?? "")
            ? funcValue!
            : "avg";
        metric = hasMetric
            ? (stringParam(params, "metric") ?? "")
            : (numberKeys[0]?.key ?? "");
        groupBy = groupSelection;
        groupByTag = boolParam(stringParam(params, "group_by_tag"));

        if (tagIds.length > 0) {
            const cache = await fetchTagsInfo(metahub_host, tagIds);
            if (token !== applyToken) return;
            selectedTags = constructTagsById(tagIds, cache);
        }
        if (token !== applyToken) return;

        const shouldRun = [
            "types",
            "tags",
            "tag_mode",
            "func",
            "metric",
            "group_by",
            "group_by_tag",
        ].some((key) => params.has(key));

        if (shouldRun) {
            await execute();
        } else {
            hasRun = false;
            groups = [];
            totalNodes = 0;
            error = null;
        }
    }

    function buildAggregateUrl(): string {
        const params = new URLSearchParams();
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

        params.set("func", func);
        params.set("metric", metric);

        const groupCsv = encodeCsv(
            Object.keys(groupBy).filter((key) => groupBy[key]),
        );
        if (groupCsv) params.set("group_by", groupCsv);
        if (groupByTag) params.set("group_by_tag", "1");

        return params.toString();
    }

    function syncUrl() {
        const search = buildAggregateUrl();
        const canonical = canonicalSearch(search);
        if (canonical === lastApplied) return;
        lastApplied = canonical;
        router.navigate("/aggregate", { search, scrollToTop: false });
    }

    async function execute() {
        const token = ++runToken;
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
            if (token !== runToken) return;
            groups = data.groups;
            totalNodes = data.total_nodes;
        } catch (e: any) {
            if (token === runToken) error = e.message || "Aggregate failed";
        } finally {
            if (token === runToken) loading = false;
        }
    }

    async function runNow() {
        syncUrl();
        await execute();
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
                            <option value={k.key}>
                                {k.label || k.key}{fieldSources(k.key) ? ` (${fieldSources(k.key)})` : ""}
                            </option>
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
                            <span class="form-check-label">
                                {k.label || k.key}
                                {#if fieldSources(k.key)}
                                    <span class="small text-secondary">({fieldSources(k.key)})</span>
                                {/if}
                            </span>
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
            <Button color="primary" size="sm" onclick={runNow}>Run</Button>
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
