<script lang="ts">
    import { Col, Row } from "@sveltestrap/sveltestrap";
    import type { TypeViewerProps } from "../lib/processor";

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
    const seriesColors = ["#49a9a7", "#e74c3c", "#f39c12", "#2ecc71", "#9b59b6", "#3498db", "#e67e22", "#1abc9c"]
    function seriesColor(idx: number): string {
        return seriesColors[idx % seriesColors.length]
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
    <Row>
        <Col xs="3">
            <div class="sidebar">
                <h6>通道选择</h6>
                <div class="checkbox-list">
                    {#each channelNames as name}
                        <label class="check-item">
                            <input type="checkbox" checked={selectedChannels.has(name)} onchange={() => toggleChannel(name)} />
                            {name}
                        </label>
                    {/each}
                </div>
                <h6>图表类型</h6>
                <div class="radio-list">
                    <label class="radio-item"><input type="radio" bind:group={chartType} value="line" /> 折线</label>
                    <label class="radio-item"><input type="radio" bind:group={chartType} value="bar" /> 柱状</label>
                    <label class="radio-item"><input type="radio" bind:group={chartType} value="scatter" /> 散点</label>
                </div>
                <h6>聚合方式</h6>
                <select bind:value={aggMethod} class="form-select">
                    <option value="mean">均值</option>
                    <option value="median">中位数</option>
                    <option value="min">最小值</option>
                    <option value="max">最大值</option>
                </select>
            </div>
        </Col>
        <Col xs="9">
            <div class="main-area">
                {#if chartData}
                    {@const { allSeries, sortedRowKeys, yMin, yMax, xStep } = chartData}
                    <svg viewBox="0 0 {chartWidth} {chartHeight}" class="chart-svg">
                        <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + plotH} stroke="#ccc" />
                        <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="#ccc" />
                        {#each yTicks as tick}
                            {@const y = scaleY(tick, yMin, yMax)}
                            <line x1={margin.left} y1={y} x2={margin.left + plotW} y2={y} stroke="#eee" stroke-dasharray="4,4" />
                            <text x={margin.left - 8} y={y + 4} text-anchor="end" font-size="11" fill="#666">{fmtNum(tick)}</text>
                        {/each}
                        {#each sortedRowKeys as rk, idx}
                            {@const x = scaleX(idx, xStep)}
                            <line x1={x} y1={margin.top + plotH} x2={x} y2={margin.top + plotH + 5} stroke="#999" />
                            <text x={x} y={margin.top + plotH + 18} text-anchor="middle" font-size="10" fill="#666" transform="rotate(-30,{x},{margin.top + plotH + 18})">{rk}</text>
                        {/each}
                        {#if chartType === "line"}
                            {#each allSeries as s, si}
                                {@const pts = s.points.map((p, i) => p.value !== null ? `${scaleX(i, xStep)},${scaleY(p.value, yMin, yMax)}` : null).filter(Boolean)}
                                {#if pts.length > 0}
                                    <polyline points={pts.join(" ")} fill="none" stroke={seriesColor(si)} stroke-width="2" />
                                    {#each s.points as p, i}
                                        {#if p.value !== null}
                                            <circle cx={scaleX(i, xStep)} cy={scaleY(p.value, yMin, yMax)} r="3" fill={seriesColor(si)} />
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
                                        <rect x={x - barWidth / 2} y={y} width={barWidth} height={plotH - (y - margin.top)} fill={seriesColor(si)} opacity="0.8" />
                                    {/if}
                                {/each}
                            {/each}
                        {:else}
                            {#each allSeries as s, si}
                                {#each s.points as p, i}
                                    {#if p.value !== null}
                                        <circle cx={scaleX(i, xStep)} cy={scaleY(p.value, yMin, yMax)} r="5" fill={seriesColor(si)} opacity="0.8" />
                                    {/if}
                                {/each}
                            {/each}
                        {/if}
                    </svg>
                    <div class="legend">
                        {#each allSeries as s, si}
                            <span class="legend-item"><span class="legend-swatch" style="background:{seriesColor(si)}"></span>{s.channelKey} / {s.itemTitle}</span>
                        {/each}
                    </div>
                {:else}
                    <p class="text-muted">Select channels to view chart.</p>
                {/if}
                {#if summaryRows.length > 0}
                    <h6 class="mt-3">统计摘要</h6>
                    <div class="table-wrap">
                        <table class="summary-table">
                            <thead>
                                <tr><th>通道</th><th>Item</th><th>Count</th><th>Mean</th><th>Min</th><th>Max</th></tr>
                            </thead>
                            <tbody>
                                {#each summaryRows as row}
                                    <tr><td>{row.channelKey}</td><td>{row.itemTitle}</td><td>{row.count}</td><td class="mono">{fmtNum(row.mean)}</td><td class="mono">{fmtNum(row.min)}</td><td class="mono">{fmtNum(row.max)}</td></tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                {/if}
            </div>
        </Col>
    </Row>
{/if}

<style>
    .sidebar { background: #f7f7f8; border-radius: 6px; padding: 12px; }
    .sidebar h6 { margin-top: 12px; margin-bottom: 6px; font-size: 0.85em; color: #555; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
    .sidebar h6:first-child { margin-top: 0; }
    .checkbox-list, .radio-list { display: flex; flex-direction: column; gap: 4px; }
    .check-item, .radio-item { font-size: 0.85em; cursor: pointer; display: flex; align-items: center; gap: 4px; }
    .form-select { width: 100%; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.85em; }
    .main-area { min-height: 200px; }
    .chart-svg { width: 100%; height: auto; border: 1px solid #eee; border-radius: 4px; background: #fff; }
    .legend { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px; }
    .legend-item { display: flex; align-items: center; gap: 4px; font-size: 0.8em; }
    .legend-swatch { width: 12px; height: 12px; border-radius: 2px; display: inline-block; }
    .table-wrap { max-height: 300px; overflow-y: auto; }
    .summary-table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
    .summary-table th, .summary-table td { padding: 3px 8px; border: 1px solid #e0e0e0; text-align: left; }
    .summary-table th { background: #f7f7f8; position: sticky; top: 0; }
    .mono { font-family: monospace; text-align: right; }
</style>
