<script lang="ts">
    import { Button, Card, CardBody } from "@sveltestrap/sveltestrap";
    import type { EditorProps } from "../registry";
    import Stack from "../../components/ui/Stack.svelte";
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

<Stack gap={3}>
    <div class="d-flex align-items-center gap-2">
        <Button size="sm" color="outline-secondary" onclick={addFormula}>+ Formula</Button>
        <span class="small text-secondary">
            In the expression, <code>x</code> is the independent variable and the remaining
            variables are adjustable coefficients (e.g. <code>a</code>, <code>b</code>).
        </span>
    </div>

    {#each formulas as f, i (i)}
        <Card>
            <CardBody>
                <div class="d-flex align-items-center gap-2">
                    <input
                        class="form-control form-control-sm fw-semibold"
                        type="text"
                        value={f.name}
                        placeholder="Formula name"
                        oninput={(e: Event) => setField(i, { name: (e.target as HTMLInputElement).value })}
                    />
                    {#if formulas.length > 1}
                        <Button
                            size="sm"
                            color="link"
                            class="text-danger px-1"
                            title="Delete formula"
                            onclick={() => removeFormula(i)}
                        >×</Button>
                    {/if}
                </div>

                <div class="d-flex align-items-center gap-2 mt-2">
                    <span class="small text-secondary text-nowrap">Expression</span>
                    <input
                        class="form-control form-control-sm font-monospace flex-grow-1"
                        type="text"
                        value={f.expression}
                        placeholder="e.g. a*x^2 + b*x + c"
                        oninput={(e: Event) => setExpression(i, (e.target as HTMLInputElement).value)}
                    />
                </div>
                {#if formulaError(f)}
                    <div class="text-danger small ms-4">{formulaError(f)}</div>
                {/if}

                <div class="d-flex align-items-center gap-2 flex-wrap mt-2">
                    <span class="small text-secondary text-nowrap">Coefficients</span>
                    {#if coefficientNames(f).length === 0}
                        <span class="text-muted small">No coefficient variables in the expression</span>
                    {:else}
                        {#each coefficientNames(f) as cname}
                            <label class="d-flex align-items-center gap-1 small">
                                <span>{cname}</span>
                                <input
                                    class="form-control form-control-sm num-input"
                                    type="number"
                                    step="any"
                                    value={Number.isFinite(f.coefficients[cname]) ? f.coefficients[cname] : 0}
                                    oninput={(e: Event) => setCoefficient(i, cname, (e.target as HTMLInputElement).value)}
                                />
                            </label>
                        {/each}
                    {/if}
                </div>

                <div class="d-flex align-items-center gap-2 flex-wrap mt-2">
                    <span class="small text-secondary text-nowrap">Domain x</span>
                    <label class="d-flex align-items-center gap-1 small">
                        <span>min</span>
                        <input
                            class="form-control form-control-sm num-input"
                            type="number"
                            step="any"
                            value={f.xmin}
                            oninput={(e: Event) => setNumberField(i, "xmin", (e.target as HTMLInputElement).value)}
                        />
                    </label>
                    <label class="d-flex align-items-center gap-1 small">
                        <span>max</span>
                        <input
                            class="form-control form-control-sm num-input"
                            type="number"
                            step="any"
                            value={f.xmax}
                            oninput={(e: Event) => setNumberField(i, "xmax", (e.target as HTMLInputElement).value)}
                        />
                    </label>
                    {#if f.xmin >= f.xmax}
                        <span class="text-warning small">min must be less than max</span>
                    {/if}
                </div>

                <div class="d-flex align-items-start gap-2 mt-2">
                    <span class="small text-secondary text-nowrap mt-1">Note</span>
                    <textarea
                        class="form-control form-control-sm"
                        rows="2"
                        value={f.note ?? ""}
                        placeholder="A short explanation of the formula (optional)"
                        oninput={(e: Event) => setField(i, { note: (e.target as HTMLTextAreaElement).value })}
                    ></textarea>
                </div>
            </CardBody>
        </Card>
    {/each}

    <Stack gap={1}>
        <span class="small text-secondary">Preview</span>
        <FormulaPlot series={previewSeries} height={300} />
    </Stack>
</Stack>

<style>
    .num-input {
        width: 5rem;
    }
</style>
