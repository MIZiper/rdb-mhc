<script lang="ts">
    import type { EditorProps } from "../registry";
    import {
        extractVariables,
        parseExpression,
        sampleCurve,
        type Coefficients,
        type FormulaDef,
    } from "../../lib/utils/formula";
    import FormulaPlot from "../../components/FormulaPlot.svelte";

    let { initial }: EditorProps = $props();

    function defaultFormula(i: number): FormulaDef {
        return {
            name: `f${i + 1}`,
            expression: "a*x + b",
            coefficients: { a: 1, b: 0 },
            xmin: -10,
            xmax: 10,
            note: "",
        };
    }

    function loadInitial(): FormulaDef[] {
        const fs = initial?.formulas;
        if (Array.isArray(fs) && fs.length > 0) {
            return fs.map((f: any, i: number) => ({
                name: typeof f?.name === "string" && f.name ? f.name : `f${i + 1}`,
                expression: typeof f?.expression === "string" ? f.expression : "",
                coefficients: { ...(f?.coefficients ?? {}) },
                xmin: typeof f?.xmin === "number" ? f.xmin : -10,
                xmax: typeof f?.xmax === "number" ? f.xmax : 10,
                note: typeof f?.note === "string" ? f.note : "",
            }));
        }
        return [defaultFormula(0)];
    }

    let formulas: FormulaDef[] = $state(loadInitial());

    function syncCoefficients(expr: string, current: Coefficients): Coefficients {
        const vars = extractVariables(expr).filter((v) => v !== "x");
        const next: Coefficients = {};
        for (const v of vars) {
            next[v] = Number.isFinite(current[v]) ? current[v] : 0;
        }
        return next;
    }

    function formulaError(f: FormulaDef): string | null {
        if (!f.expression.trim()) return "Expression is empty";
        try {
            parseExpression(f.expression);
            return null;
        } catch (e) {
            return (e as Error).message;
        }
    }

    function coefficientNames(f: FormulaDef): string[] {
        return extractVariables(f.expression).filter((v) => v !== "x");
    }

    function addFormula() {
        formulas = [...formulas, defaultFormula(formulas.length)];
    }

    function removeFormula(i: number) {
        if (formulas.length <= 1) return;
        formulas = formulas.filter((_, idx) => idx !== i);
    }

    function setField(i: number, patch: Partial<FormulaDef>) {
        formulas = formulas.map((f, idx) => (idx === i ? { ...f, ...patch } : f));
    }

    function setExpression(i: number, expr: string) {
        formulas = formulas.map((f, idx) =>
            idx === i ? { ...f, expression: expr, coefficients: syncCoefficients(expr, f.coefficients) } : f,
        );
    }

    function setCoefficient(i: number, name: string, raw: string) {
        const num = raw.trim() === "" ? 0 : parseFloat(raw);
        const value = Number.isNaN(num) ? 0 : num;
        formulas = formulas.map((f, idx) =>
            idx === i ? { ...f, coefficients: { ...f.coefficients, [name]: value } } : f,
        );
    }

    function setNumberField(i: number, field: "xmin" | "xmax", raw: string) {
        const num = parseFloat(raw);
        setField(i, { [field]: Number.isNaN(num) ? 0 : num });
    }

    let previewSeries = $derived.by(() => {
        return formulas
            .filter((f) => formulaError(f) === null)
            .map((f) => ({
                label: f.name || f.expression,
                points: sampleCurve(f, 160),
            }));
    });

    export function getContent() {
        return {
            type: "formula",
            formulas: formulas.map((f) => ({
                name: f.name,
                expression: f.expression,
                coefficients: { ...f.coefficients },
                xmin: Number(f.xmin),
                xmax: Number(f.xmax),
                note: f.note ?? "",
            })),
        };
    }
</script>

<div id="main">
    <div class="toolbar">
        <button class="btn-sm" onclick={addFormula}>+ Formula</button>
        <span class="hint">In the expression, <code>x</code> is the independent variable and the remaining variables are adjustable coefficients (e.g. <code>a</code>, <code>b</code>).</span>
    </div>

    {#each formulas as f, i (i)}
        <div class="formula-card">
            <div class="card-head">
                <input
                    class="name-input"
                    type="text"
                    value={f.name}
                    placeholder="Formula name"
                    oninput={(e: Event) => setField(i, { name: (e.target as HTMLInputElement).value })}
                />
                {#if formulas.length > 1}
                    <button class="btn-del" title="Delete formula" onclick={() => removeFormula(i)}>×</button>
                {/if}
            </div>

            <label class="field">
                <span class="field-label">Expression</span>
                <input
                    class="expr-input"
                    type="text"
                    value={f.expression}
                    placeholder="e.g. a*x^2 + b*x + c"
                    oninput={(e: Event) => setExpression(i, (e.target as HTMLInputElement).value)}
                />
            </label>
            {#if formulaError(f)}
                <div class="error">{formulaError(f)}</div>
            {/if}

            <div class="coeff-row">
                <span class="field-label">Coefficients</span>
                {#if coefficientNames(f).length === 0}
                    <span class="text-muted small">No coefficient variables in the expression</span>
                {:else}
                    {#each coefficientNames(f) as cname}
                        <label class="coeff-item">
                            <span>{cname}</span>
                            <input
                                type="number"
                                step="any"
                                value={Number.isFinite(f.coefficients[cname]) ? f.coefficients[cname] : 0}
                                oninput={(e: Event) => setCoefficient(i, cname, (e.target as HTMLInputElement).value)}
                            />
                        </label>
                    {/each}
                {/if}
            </div>

            <div class="range-row">
                <span class="field-label">Domain x</span>
                <label class="range-item">
                    <span>min</span>
                    <input
                        type="number"
                        step="any"
                        value={f.xmin}
                        oninput={(e: Event) => setNumberField(i, "xmin", (e.target as HTMLInputElement).value)}
                    />
                </label>
                <label class="range-item">
                    <span>max</span>
                    <input
                        type="number"
                        step="any"
                        value={f.xmax}
                        oninput={(e: Event) => setNumberField(i, "xmax", (e.target as HTMLInputElement).value)}
                    />
                </label>
                {#if f.xmin >= f.xmax}
                    <span class="warn">min must be less than max</span>
                {/if}
            </div>

            <label class="field">
                <span class="field-label">Note</span>
                <textarea
                    rows="2"
                    value={f.note ?? ""}
                    placeholder="A short explanation of the formula (optional)"
                    oninput={(e: Event) => setField(i, { note: (e.target as HTMLTextAreaElement).value })}
                ></textarea>
            </label>
        </div>
    {/each}

    <div class="preview">
        <span class="field-label">Preview</span>
        <FormulaPlot series={previewSeries} height={300} />
    </div>
</div>

<style>
    #main {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .toolbar {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hint {
        font-size: 0.78em;
        color: #888;
    }
    .hint code {
        background: #f0f0f0;
        padding: 0 3px;
        border-radius: 2px;
    }
    .btn-sm {
        padding: 2px 10px;
        border: 1px solid #999;
        border-radius: 4px;
        background: #fff;
        cursor: pointer;
        font-size: 0.85em;
    }
    .formula-card {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        background: #fafafa;
    }
    .card-head {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .name-input {
        flex: 1;
        font-weight: 600;
        border: 1px solid #ddd;
        border-radius: 3px;
        padding: 3px 6px;
    }
    .btn-del {
        border: none;
        background: none;
        color: #c00;
        cursor: pointer;
        font-weight: bold;
        font-size: 1.1em;
        padding: 0 4px;
    }
    .field {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .field-label {
        font-size: 0.8em;
        color: #666;
        min-width: 52px;
        flex-shrink: 0;
    }
    .expr-input {
        flex: 1;
        font-family: monospace;
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 4px 6px;
    }
    .coeff-row,
    .range-row {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .coeff-item,
    .range-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 0.85em;
    }
    .coeff-item input {
        width: 80px;
    }
    .range-item input {
        width: 90px;
    }
    .coeff-item input,
    .range-item input {
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 3px 5px;
    }
    textarea {
        flex: 1;
        font-size: 0.85em;
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 4px 6px;
        resize: vertical;
    }
    .error {
        color: #b00020;
        font-size: 0.82em;
        margin-left: 60px;
    }
    .warn {
        color: #b06a00;
        font-size: 0.8em;
    }
    .small {
        font-size: 0.8em;
    }
    .preview {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
</style>
