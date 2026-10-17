<script lang="ts">
    import { Card, CardBody, Input, Table } from "@sveltestrap/sveltestrap";
    import type { ViewerProps } from "../registry";
    import Stack from "../../components/ui/Stack.svelte";
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
    <Stack gap={3}>
        <FormulaPlot {series} height={380} />

        <div class="d-flex flex-column gap-2">
            <label class="d-flex align-items-center gap-2">
                <span>independent variable x =</span>
                <Input type="number" step="any" class="w-auto" bind:value={xInput} />
            </label>
            {#if !Number.isFinite(xValue)}
                <span class="text-warning small">Enter a valid number</span>
            {/if}
            <Table bordered size="sm" class="small align-middle eval-table">
                <thead>
                    <tr><th>Formula</th><th>y(x)</th></tr>
                </thead>
                <tbody>
                    {#each evaluations as row}
                        <tr>
                            <td>{row.name}</td>
                            <td class="font-monospace">
                                {#if row.y === null}
                                    <span class="text-secondary fst-italic">Out of domain / undefined</span>
                                {:else}
                                    {fmt(row.y)}
                                {/if}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </Table>
        </div>

        <Stack gap={2}>
            {#each formulas as f}
                <Card>
                    <CardBody>
                        <div class="d-flex justify-content-between align-items-baseline gap-3">
                            <span class="fw-semibold">{f.name}</span>
                            <span class="small text-secondary">x ∈ [{fmt(f.xmin)}, {fmt(f.xmax)}]</span>
                        </div>
                        <code class="d-block font-monospace small text-success mt-1 text-break">{f.expression}</code>
                        {#if coeffText(f)}
                            <div class="small text-secondary mt-1">Coefficients: {coeffText(f)}</div>
                        {/if}
                        {#if f.note}
                            <div class="small text-secondary mt-2 border-start border-3 ps-2">{f.note}</div>
                        {/if}
                    </CardBody>
                </Card>
            {/each}
        </Stack>
    </Stack>
{/if}

<style>
    :global(.eval-table) {
        max-width: 480px;
    }
</style>
