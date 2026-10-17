<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardHeader,
        Col,
        Row,
    } from "@sveltestrap/sveltestrap";
    import type { TypeViewerProps } from "../registry";
    import { parseFormulaContent, sampleCurve, type FormulaDef } from "../../lib/utils/formula";
    import FormulaPlot from "../../components/FormulaPlot.svelte";

    interface ParsedItem {
        title: string;
        formulas: FormulaDef[];
    }

    interface Entry {
        key: string;
        itemTitle: string;
        formula: FormulaDef;
    }

    let { items }: TypeViewerProps = $props();

    let parsedItems: ParsedItem[] = $derived.by(() => {
        const out: ParsedItem[] = [];
        for (const it of items) {
            const content = parseFormulaContent(it.content);
            if (content && content.formulas.length > 0) {
                out.push({ title: it.title, formulas: content.formulas });
            }
        }
        return out;
    });

    let entries: Entry[] = $derived.by(() => {
        const out: Entry[] = [];
        parsedItems.forEach((it, ii) => {
            it.formulas.forEach((f, fi) => {
                out.push({ key: `${ii}:${fi}`, itemTitle: it.title, formula: f });
            });
        });
        return out;
    });

    let selected: Set<string> = $state(new Set());
    let initialized: boolean = $state(false);

    $effect(() => {
        if (!initialized && entries.length > 0) {
            selected = new Set(entries.map((e) => e.key));
            initialized = true;
        }
    });

    function toggle(key: string) {
        const next = new Set(selected);
        if (next.has(key)) next.delete(key);
        else next.add(key);
        selected = next;
    }

    let series = $derived.by(() =>
        entries
            .filter((e) => selected.has(e.key))
            .map((e) => ({
                label: `${e.itemTitle} / ${e.formula.name}`,
                points: sampleCurve(e.formula, 200),
            })),
    );
</script>

{#if parsedItems.length === 0}
    <p class="text-muted">No valid Formula data in selected items.</p>
{:else}
    <Row class="g-3">
        <Col xs="3">
            <Card>
                <CardHeader class="py-2 fw-semibold">Formula selection</CardHeader>
                <CardBody class="pt-2">
                    <div class="d-flex gap-2 mb-2">
                        <Button size="sm" color="outline-secondary" onclick={() => (selected = new Set(entries.map((e) => e.key)))}>Select all</Button>
                        <Button size="sm" color="outline-secondary" onclick={() => (selected = new Set())}>Clear</Button>
                    </div>
                    <div class="checkbox-list">
                        {#each entries as e (e.key)}
                            <label class="form-check mb-1">
                                <input
                                    class="form-check-input mt-1"
                                    type="checkbox"
                                    checked={selected.has(e.key)}
                                    onchange={() => toggle(e.key)}
                                />
                                <span class="form-check-label">
                                    <span class="d-block fw-medium">{e.itemTitle}</span>
                                    <span class="d-block small text-secondary">{e.formula.name}</span>
                                </span>
                            </label>
                        {/each}
                    </div>
                </CardBody>
            </Card>
        </Col>
        <Col xs="9">
            <div class="main-area">
                {#if series.length > 0}
                    <FormulaPlot {series} height={420} />
                {:else}
                    <p class="text-muted">Select formulas to view chart.</p>
                {/if}
            </div>
        </Col>
    </Row>
{/if}

<style>
    .checkbox-list {
        max-height: 60vh;
        overflow-y: auto;
    }
    .main-area {
        min-height: 200px;
    }
</style>
