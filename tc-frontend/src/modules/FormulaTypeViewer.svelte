<script lang="ts">
    import { Col, Row } from "@sveltestrap/sveltestrap";
    import type { TypeViewerProps } from "../lib/processor";
    import { parseFormulaContent, sampleCurve, type FormulaDef } from "../lib/formula";
    import FormulaPlot from "./FormulaPlot.svelte";

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
    <Row>
        <Col xs="3">
            <div class="sidebar">
                <h6>公式选择</h6>
                <div class="toggle-row">
                    <button class="mini" onclick={() => (selected = new Set(entries.map((e) => e.key)))}>全选</button>
                    <button class="mini" onclick={() => (selected = new Set())}>清空</button>
                </div>
                <div class="checkbox-list">
                    {#each entries as e (e.key)}
                        <label class="check-item">
                            <input type="checkbox" checked={selected.has(e.key)} onchange={() => toggle(e.key)} />
                            <span>
                                <span class="item-title">{e.itemTitle}</span>
                                <span class="formula-name">{e.formula.name}</span>
                            </span>
                        </label>
                    {/each}
                </div>
            </div>
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
    .sidebar {
        background: #f7f7f8;
        border-radius: 6px;
        padding: 12px;
    }
    .sidebar h6 {
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 0.85em;
        color: #555;
        border-bottom: 1px solid #ddd;
        padding-bottom: 4px;
    }
    .toggle-row {
        display: flex;
        gap: 6px;
        margin-bottom: 8px;
    }
    .mini {
        border: 1px solid #ccc;
        border-radius: 3px;
        background: #fff;
        cursor: pointer;
        font-size: 0.78em;
        padding: 1px 8px;
    }
    .checkbox-list {
        display: flex;
        flex-direction: column;
        gap: 4px;
        max-height: 60vh;
        overflow-y: auto;
    }
    .check-item {
        font-size: 0.85em;
        cursor: pointer;
        display: flex;
        align-items: flex-start;
        gap: 6px;
    }
    .check-item input {
        margin-top: 2px;
        flex-shrink: 0;
    }
    .item-title {
        display: block;
        font-weight: 500;
    }
    .formula-name {
        display: block;
        color: #888;
        font-size: 0.9em;
    }
    .main-area {
        min-height: 200px;
    }
</style>
