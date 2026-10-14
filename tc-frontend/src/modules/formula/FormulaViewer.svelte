<script lang="ts">
    import type { ViewerProps } from "../registry";
    import {
        evaluateFormulaAt,
        parseFormulaContent,
        sampleCurve,
        type FormulaContent,
    } from "../../lib/utils/formula";
    import FormulaPlot from "../../components/FormulaPlot.svelte";

    let { content_in }: ViewerProps = $props();

    let content: FormulaContent | null = $derived(parseFormulaContent(content_in));
    let formulas = $derived(content?.formulas ?? []);

    let xInput: string = $state("0");
    let xValue = $derived(parseFloat(xInput));

    let series = $derived.by(() =>
        formulas.map((f) => ({
            label: f.name || f.expression,
            points: sampleCurve(f, 240),
        })),
    );

    let evaluations = $derived.by(() => {
        const x = xValue;
        return formulas.map((f) => ({
            name: f.name || f.expression,
            y: Number.isFinite(x) ? evaluateFormulaAt(f, x) : null,
        }));
    });

    function fmt(n: number): string {
        if (!Number.isFinite(n)) return "—";
        const abs = Math.abs(n);
        if (abs !== 0 && (abs < 0.0001 || abs >= 1e6)) return n.toExponential(3);
        return Number(n.toFixed(6)).toString();
    }

    function coeffText(f: { coefficients: Record<string, number> }): string {
        const entries = Object.entries(f.coefficients ?? {});
        if (entries.length === 0) return "";
        return entries.map(([k, v]) => `${k}=${fmt(v)}`).join(", ");
    }
</script>

{#if formulas.length === 0}
    <p class="text-muted">No formula data</p>
{:else}
    <div class="viewer">
        <FormulaPlot {series} height={380} />

        <div class="eval-panel">
            <label class="x-input">
                <span>independent variable x =</span>
                <input type="number" step="any" bind:value={xInput} />
            </label>
            {#if !Number.isFinite(xValue)}
                <span class="warn">Enter a valid number</span>
            {/if}
            <table class="eval-table">
                <thead>
                    <tr><th>Formula</th><th>y(x)</th></tr>
                </thead>
                <tbody>
                    {#each evaluations as row}
                        <tr>
                            <td>{row.name}</td>
                            <td class="mono">
                                {#if row.y === null}
                                    <span class="null-cell">Out of domain / undefined</span>
                                {:else}
                                    {fmt(row.y)}
                                {/if}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>

        <div class="formula-list">
            {#each formulas as f}
                <div class="formula-item">
                    <div class="formula-head">
                        <span class="fname">{f.name}</span>
                        <span class="fdomain">x ∈ [{fmt(f.xmin)}, {fmt(f.xmax)}]</span>
                    </div>
                    <code class="fexpr">{f.expression}</code>
                    {#if coeffText(f)}
                        <div class="fcoeff">Coefficients: {coeffText(f)}</div>
                    {/if}
                    {#if f.note}
                        <div class="fnote">{f.note}</div>
                    {/if}
                </div>
            {/each}
        </div>
    </div>
{/if}

<style>
    .viewer {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .eval-panel {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .x-input {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9em;
    }
    .x-input input {
        width: 140px;
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 4px 6px;
    }
    .warn {
        color: #b06a00;
        font-size: 0.82em;
    }
    .eval-table {
        border-collapse: collapse;
        width: 100%;
        max-width: 480px;
        font-size: 0.88em;
    }
    .eval-table th,
    .eval-table td {
        border: 1px solid #e0e0e0;
        padding: 4px 8px;
        text-align: left;
    }
    .eval-table th {
        background: #f7f7f8;
    }
    .mono {
        font-family: monospace;
    }
    .null-cell {
        color: #bbb;
        font-style: italic;
    }
    .formula-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .formula-item {
        background: #fafafa;
        border: 1px solid #e8e8e8;
        border-radius: 6px;
        padding: 10px 12px;
    }
    .formula-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 12px;
    }
    .fname {
        font-weight: 600;
        color: #333;
    }
    .fdomain {
        font-size: 0.8em;
        color: #888;
    }
    .fexpr {
        display: block;
        font-family: monospace;
        font-size: 0.9em;
        color: #1a6;
        margin-top: 4px;
        word-break: break-all;
    }
    .fcoeff {
        font-size: 0.82em;
        color: #666;
        margin-top: 4px;
    }
    .fnote {
        font-size: 0.85em;
        color: #555;
        margin-top: 6px;
        border-left: 3px solid #49a9a7;
        padding-left: 8px;
    }
</style>
