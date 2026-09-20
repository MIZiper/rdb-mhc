<script lang="ts">
    import type { Point } from "../lib/formula";

    interface PlotSeries {
        label: string;
        points: Point[];
        color?: string;
    }

    let {
        series,
        width = 760,
        height = 360,
        xLabel = "x",
        yLabel = "y",
        showPoints = true,
    }: {
        series: PlotSeries[];
        width?: number;
        height?: number;
        xLabel?: string;
        yLabel?: string;
        showPoints?: boolean;
    } = $props();

    const margin = { top: 20, right: 20, bottom: 44, left: 60 };
    const plotW = $derived(width - margin.left - margin.right);
    const plotH = $derived(height - margin.top - margin.bottom);

    const palette = [
        "#49a9a7",
        "#e74c3c",
        "#f39c12",
        "#2ecc71",
        "#9b59b6",
        "#3498db",
        "#e67e22",
        "#1abc9c",
        "#d35400",
        "#34495e",
    ];

    function color(i: number): string {
        return series[i]?.color || palette[i % palette.length];
    }

    const bounds = $derived.by(() => {
        let xMin = Infinity;
        let xMax = -Infinity;
        let yMin = Infinity;
        let yMax = -Infinity;
        for (const s of series) {
            for (const p of s.points) {
                if (p.x < xMin) xMin = p.x;
                if (p.x > xMax) xMax = p.x;
                if (p.y < yMin) yMin = p.y;
                if (p.y > yMax) yMax = p.y;
            }
        }
        if (!Number.isFinite(xMin) || !Number.isFinite(yMin)) return null;
        if (xMin === xMax) {
            xMin -= 1;
            xMax += 1;
        }
        const yPad = (yMax - yMin) * 0.1 || 1;
        if (yMin === yMax) {
            yMin -= 1;
            yMax += 1;
        } else {
            yMin -= yPad;
            yMax += yPad;
        }
        return { xMin, xMax, yMin, yMax };
    });

    function scaleX(x: number, xMin: number, xMax: number): number {
        return margin.left + ((x - xMin) / (xMax - xMin)) * plotW;
    }

    function scaleY(y: number, yMin: number, yMax: number): number {
        return margin.top + plotH - ((y - yMin) / (yMax - yMin)) * plotH;
    }

    function fmtNum(n: number): string {
        if (!Number.isFinite(n)) return String(n);
        const abs = Math.abs(n);
        if (abs !== 0 && (abs < 0.001 || abs >= 100000)) return n.toExponential(2);
        return Number(n.toFixed(4)).toString();
    }

    const yTicks = $derived.by(() => {
        if (!bounds) return [];
        const step = (bounds.yMax - bounds.yMin) / 5;
        return Array.from({ length: 6 }, (_, i) => bounds.yMin + step * i);
    });

    const xTicks = $derived.by(() => {
        if (!bounds) return [];
        const step = (bounds.xMax - bounds.xMin) / 5;
        return Array.from({ length: 6 }, (_, i) => bounds.xMin + step * i);
    });
</script>

{#if !bounds}
    <p class="text-muted">暂无可绘制的数据点</p>
{:else}
    {@const { xMin, xMax, yMin, yMax } = bounds}
    <svg viewBox="0 0 {width} {height}" class="formula-svg" role="img" aria-label="formula plot">
        {#each yTicks as tick}
            {@const y = scaleY(tick, yMin, yMax)}
            <line x1={margin.left} y1={y} x2={margin.left + plotW} y2={y} stroke="#eee" stroke-dasharray="4,4" />
            <text x={margin.left - 8} y={y + 4} text-anchor="end" font-size="11" fill="#666">{fmtNum(tick)}</text>
        {/each}
        {#each xTicks as tick}
            {@const x = scaleX(tick, xMin, xMax)}
            <line x1={x} y1={margin.top} x2={x} y2={margin.top + plotH} stroke="#f5f5f5" />
            <line x1={x} y1={margin.top + plotH} x2={x} y2={margin.top + plotH + 5} stroke="#999" />
            <text x={x} y={margin.top + plotH + 18} text-anchor="middle" font-size="11" fill="#666">{fmtNum(tick)}</text>
        {/each}
        <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + plotH} stroke="#ccc" />
        <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="#ccc" />
        <text x={margin.left + plotW} y={margin.top + plotH + 36} text-anchor="end" font-size="12" fill="#555">{xLabel}</text>
        <text x={margin.left - 44} y={margin.top + 4} text-anchor="start" font-size="12" fill="#555">{yLabel}</text>

        {#each series as s, si}
            {@const pts = s.points.map((p) => `${scaleX(p.x, xMin, xMax)},${scaleY(p.y, yMin, yMax)}`)}
            {#if pts.length > 0}
                <polyline points={pts.join(" ")} fill="none" stroke={color(si)} stroke-width="2" />
                {#if showPoints}
                    {#each s.points as p}
                        <circle cx={scaleX(p.x, xMin, xMax)} cy={scaleY(p.y, yMin, yMax)} r="2.5" fill={color(si)} />
                    {/each}
                {/if}
            {/if}
        {/each}
    </svg>
    <div class="legend">
        {#each series as s, si}
            <span class="legend-item"><span class="legend-swatch" style="background:{color(si)}"></span>{s.label}</span>
        {/each}
    </div>
{/if}

<style>
    .formula-svg {
        width: 100%;
        height: auto;
        border: 1px solid #eee;
        border-radius: 4px;
        background: #fff;
    }
    .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 8px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 0.8em;
    }
    .legend-swatch {
        width: 12px;
        height: 12px;
        border-radius: 2px;
        display: inline-block;
    }
</style>
