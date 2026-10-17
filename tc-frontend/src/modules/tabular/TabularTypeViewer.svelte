<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardHeader,
        Col,
        Input,
        Row,
        Table,
    } from "@sveltestrap/sveltestrap";
    import type { TypeViewerProps } from "../registry";
    import Legend from "../../components/ui/Legend.svelte";
    import { chartColor } from "../../lib/utils/ui";

    interface DataRow {
        id_idx?: string | null
        time: number
        value: number
    }

    interface Channel {
        name: string
        id_name?: string | null
        data: DataRow[]
    }

    interface ItemContent {
        title: string
        channels: Channel[]
    }

    let { items }: TypeViewerProps = $props();

    let parsedItems: ItemContent[] = $derived.by(() => {
        return items
            .map(it => {
                const content = typeof it.content === "string" ? JSON.parse(it.content) : it.content
                if (content?.channels && Array.isArray(content.channels)) {
                    return { title: it.title, channels: content.channels as Channel[] }
                }
                return null
            })
            .filter(Boolean) as ItemContent[]
    })

    let channelNames: string[] = $derived.by(() => {
        const s = new Set<string>()
        for (const item of parsedItems) {
            for (const ch of item.channels) {
                s.add(ch.id_name || ch.name)
            }
        }
        return [...s]
    })

    let selectedChannels: Set<string> = $state(new Set())
    let chartType: "line" | "bar" | "scatter" = $state("line")
    let aggMethod: "mean" | "median" | "min" | "max" = $state("mean")

    $effect(() => {
        if (selectedChannels.size === 0) {
            selectedChannels = new Set(channelNames)
        }
    })

    function toggleChannel(name: string) {
        const next = new Set(selectedChannels)
        if (next.has(name)) next.delete(name)
        else next.add(name)
        selectedChannels = next
    }

    function channelKey(ch: Channel): string {
        return ch.id_name || ch.name
    }

    function rowKey(row: DataRow, rowIdx: number): string {
        return row.id_idx || String(rowIdx)
    }

    interface AggRow {
        channelKey: string
        itemTitle: string
        rowKey: string
        values: number[]
    }

    let aggregated = $derived.by(() => {
        const grouped = new Map<string, Map<string, Map<string, number[]>>>()
        for (const item of parsedItems) {
            for (const ch of item.channels) {
                const ck = channelKey(ch)
                ch.data.forEach((row, idx) => {
                    const rk = rowKey(row, idx)
                    if (!grouped.has(ck)) grouped.set(ck, new Map())
                    const im = grouped.get(ck)!
                    if (!im.has(item.title)) im.set(item.title, new Map())
                    const rm = im.get(item.title)!
                    if (!rm.has(rk)) rm.set(rk, [])
                    rm.get(rk)!.push(row.value)
                })
            }
        }
        return grouped
    })

    function computeAgg(values: number[]): number {
        if (values.length === 0) return 0
        const sorted = [...values].sort((a, b) => a - b)
        switch (aggMethod) {
            case "mean": return values.reduce((s, v) => s + v, 0) / values.length
            case "median": {
                const mid = Math.floor(sorted.length / 2)
                return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
            }
            case "min": return sorted[0]
            case "max": return sorted[sorted.length - 1]
        }
    }

    interface SeriesPoint {
        rowKey: string
        value: number | null
    }

    interface Series {
        channelKey: string
        itemTitle: string
        points: SeriesPoint[]
    }

    let chartSeries = $derived.by(() => {
        const series: Series[] = []
        const allRowKeys = new Set<string>()
        for (const [ck, itemMap] of aggregated) {
            if (!selectedChannels.has(ck)) continue
            for (const [, rowMap] of itemMap) {
                for (const rk of rowMap.keys()) allRowKeys.add(rk)
            }
        }
        const sortedRowKeys = [...allRowKeys].sort()
        for (const [ck, itemMap] of aggregated) {
            if (!selectedChannels.has(ck)) continue
            for (const [itemTitle, rowMap] of itemMap) {
                const points: SeriesPoint[] = sortedRowKeys.map(rk => {
                    const vals = rowMap.get(rk)
                    return vals ? { rowKey: rk, value: computeAgg(vals) } : { rowKey: rk, value: null }
                })
                series.push({ channelKey: ck, itemTitle, points })
            }
        }
        return { series, sortedRowKeys }
    })

    let summaryRows = $derived.by(() => {
        const rows: { channelKey: string; itemTitle: string; count: number; mean: number; min: number; max: number }[] = []
        for (const [ck, itemMap] of aggregated) {
            if (!selectedChannels.has(ck)) continue
            for (const [itemTitle, rowMap] of itemMap) {
                const allVals: number[] = []
                for (const vals of rowMap.values()) allVals.push(...vals)
                if (allVals.length === 0) continue
                const sorted = [...allVals].sort((a, b) => a - b)
                rows.push({
                    channelKey: ck, itemTitle, count: allVals.length,
                    mean: allVals.reduce((s, v) => s + v, 0) / allVals.length,
                    min: sorted[0], max: sorted[sorted.length - 1],
                })
            }
        }
        return rows
    })

    const chartWidth = 800
    const chartHeight = 400
    const margin = { top: 20, right: 20, bottom: 60, left: 60 }
    const plotW = chartWidth - margin.left - margin.right
    const plotH = chartHeight - margin.top - margin.bottom

    let chartData = $derived.by(() => {
        const { series: allSeries, sortedRowKeys } = chartSeries
        if (sortedRowKeys.length === 0 || allSeries.length === 0) return null
        let yMin = Infinity, yMax = -Infinity
        for (const s of allSeries) {
            for (const p of s.points) {
                if (p.value !== null) {
                    if (p.value < yMin) yMin = p.value
                    if (p.value > yMax) yMax = p.value
                }
            }
        }
        if (!isFinite(yMin)) yMin = 0
        if (!isFinite(yMax)) yMax = 1
        const yPad = (yMax - yMin) * 0.1 || 1
        yMin -= yPad; yMax += yPad
        const xStep = sortedRowKeys.length > 1 ? plotW / (sortedRowKeys.length - 1) : plotW / 2
        return { allSeries, sortedRowKeys, yMin, yMax, xStep }
    })

    function scaleY(val: number, yMin: number, yMax: number): number {
        return margin.top + plotH - ((val - yMin) / (yMax - yMin)) * plotH
    }
    function scaleX(idx: number, xStep: number): number {
        return margin.left + (idx * xStep)
    }
    function fmtNum(n: number): string {
        return Number.isFinite(n) ? n.toFixed(4).replace(/\.?0+$/, "") : String(n)
    }
    let yTicks = $derived.by(() => {
        if (!chartData) return []
        const { yMin, yMax } = chartData
        const step = (yMax - yMin) / 5
        const ticks: number[] = []
        for (let i = 0; i <= 5; i++) ticks.push(yMin + step * i)
        return ticks
    })
</script>

{#if parsedItems.length === 0}
    <p class="text-muted">No valid Tabular data in selected items.</p>
{:else}
    <Row class="g-3">
        <Col xs="3">
            <Card>
                <CardHeader class="py-2 fw-semibold">Channels</CardHeader>
                <CardBody class="pt-2">
                    <div class="checkbox-list">
                        {#each channelNames as name}
                            <label class="form-check mb-1">
                                <input
                                    class="form-check-input"
                                    type="checkbox"
                                    checked={selectedChannels.has(name)}
                                    onchange={() => toggleChannel(name)}
                                />
                                <span class="form-check-label">{name}</span>
                            </label>
                        {/each}
                    </div>

                    <div class="fw-semibold border-bottom pb-1 mb-2 mt-3">Chart type</div>
                    <label class="form-check mb-1">
                        <input class="form-check-input" type="radio" bind:group={chartType} value="line" />
                        <span class="form-check-label">Line</span>
                    </label>
                    <label class="form-check mb-1">
                        <input class="form-check-input" type="radio" bind:group={chartType} value="bar" />
                        <span class="form-check-label">Bar</span>
                    </label>
                    <label class="form-check">
                        <input class="form-check-input" type="radio" bind:group={chartType} value="scatter" />
                        <span class="form-check-label">Scatter</span>
                    </label>

                    <div class="fw-semibold border-bottom pb-1 mb-2 mt-3">Aggregation</div>
                    <Input type="select" bsSize="sm" bind:value={aggMethod}>
                        <option value="mean">Mean</option>
                        <option value="median">Median</option>
                        <option value="min">Min</option>
                        <option value="max">Max</option>
                    </Input>
                </CardBody>
            </Card>
        </Col>
        <Col xs="9">
            <div class="main-area">
                {#if chartData}
                    {@const { allSeries, sortedRowKeys, yMin, yMax, xStep } = chartData}
                    <svg viewBox="0 0 {chartWidth} {chartHeight}" class="chart-svg">
                        <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + plotH} stroke="var(--bs-border-color)" />
                        <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="var(--bs-border-color)" />
                        {#each yTicks as tick}
                            {@const y = scaleY(tick, yMin, yMax)}
                            <line x1={margin.left} y1={y} x2={margin.left + plotW} y2={y} stroke="var(--bs-border-color-translucent)" stroke-dasharray="4,4" />
                            <text x={margin.left - 8} y={y + 4} text-anchor="end" font-size="11" fill="var(--bs-secondary-color)">{fmtNum(tick)}</text>
                        {/each}
                        {#each sortedRowKeys as rk, idx}
                            {@const x = scaleX(idx, xStep)}
                            <line x1={x} y1={margin.top + plotH} x2={x} y2={margin.top + plotH + 5} stroke="var(--bs-border-color)" />
                            <text x={x} y={margin.top + plotH + 18} text-anchor="middle" font-size="10" fill="var(--bs-secondary-color)" transform="rotate(-30,{x},{margin.top + plotH + 18})">{rk}</text>
                        {/each}
                        {#if chartType === "line"}
                            {#each allSeries as s, si}
                                {@const pts = s.points.map((p, i) => p.value !== null ? `${scaleX(i, xStep)},${scaleY(p.value, yMin, yMax)}` : null).filter(Boolean)}
                                {#if pts.length > 0}
                                    <polyline points={pts.join(" ")} fill="none" stroke={chartColor(si)} stroke-width="2" />
                                    {#each s.points as p, i}
                                        {#if p.value !== null}
                                            <circle cx={scaleX(i, xStep)} cy={scaleY(p.value, yMin, yMax)} r="3" fill={chartColor(si)} />
                                        {/if}
                                    {/each}
                                {/if}
                            {/each}
                        {:else if chartType === "bar"}
                            {@const barWidth = Math.max(3, (xStep * 0.7) / allSeries.length)}
                            {#each allSeries as s, si}
                                {#each s.points as p, i}
                                    {#if p.value !== null}
                                        {@const x = scaleX(i, xStep) - (allSeries.length * barWidth) / 2 + si * barWidth + barWidth / 2}
                                        {@const y = scaleY(p.value, yMin, yMax)}
                                        <rect x={x - barWidth / 2} y={y} width={barWidth} height={plotH - (y - margin.top)} fill={chartColor(si)} opacity="0.8" />
                                    {/if}
                                {/each}
                            {/each}
                        {:else}
                            {#each allSeries as s, si}
                                {#each s.points as p, i}
                                    {#if p.value !== null}
                                        <circle cx={scaleX(i, xStep)} cy={scaleY(p.value, yMin, yMax)} r="5" fill={chartColor(si)} opacity="0.8" />
                                    {/if}
                                {/each}
                            {/each}
                        {/if}
                    </svg>
                    <Legend
                        class="mt-2"
                        items={allSeries.map((s, si) => ({ label: `${s.channelKey} / ${s.itemTitle}`, color: chartColor(si) }))}
                    />
                {:else}
                    <p class="text-muted">Select channels to view chart.</p>
                {/if}
                {#if summaryRows.length > 0}
                    <h6 class="mt-3">Summary</h6>
                    <div class="summary-wrap">
                        <Table bordered hover size="sm" class="small align-middle mb-0">
                            <thead class="sticky-top">
                                <tr><th>Channel</th><th>Item</th><th>Count</th><th>Mean</th><th>Min</th><th>Max</th></tr>
                            </thead>
                            <tbody>
                                {#each summaryRows as row}
                                    <tr><td>{row.channelKey}</td><td>{row.itemTitle}</td><td>{row.count}</td><td class="font-monospace text-end">{fmtNum(row.mean)}</td><td class="font-monospace text-end">{fmtNum(row.min)}</td><td class="font-monospace text-end">{fmtNum(row.max)}</td></tr>
                                {/each}
                            </tbody>
                        </Table>
                    </div>
                {/if}
            </div>
        </Col>
    </Row>
{/if}

<style>
    .checkbox-list {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        max-height: 60vh;
        overflow-y: auto;
    }
    .main-area {
        min-height: 200px;
    }
    .chart-svg {
        width: 100%;
        height: auto;
        border: 1px solid var(--bs-border-color);
        border-radius: var(--bs-border-radius);
        background: var(--bs-body-bg);
    }
    .summary-wrap {
        max-height: 300px;
        overflow-y: auto;
    }
</style>
