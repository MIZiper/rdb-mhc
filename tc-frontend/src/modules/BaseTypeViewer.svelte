<script lang="ts">
    import type { TypeViewerProps } from "../lib/processor";

    let { items }: TypeViewerProps = $props();

    function formatLines(obj: any, prefix: string = ""): { label: string; value: string }[] {
        if (obj === null || obj === undefined) return [{ label: prefix, value: "null" }];
        if (typeof obj !== "object") return [{ label: prefix, value: JSON.stringify(obj) }];
        if (Array.isArray(obj)) {
            const lines: { label: string; value: string }[] = [];
            for (let i = 0; i < obj.length; i++) {
                lines.push(...formatLines(obj[i], `${prefix}[${i}]`));
            }
            return lines;
        }
        const lines: { label: string; value: string }[] = [];
        for (const [key, val] of Object.entries(obj)) {
            const fullKey = prefix ? `${prefix}.${key}` : key;
            if (val === null || val === undefined) {
                lines.push({ label: fullKey, value: "null" });
            } else if (typeof val !== "object") {
                lines.push({ label: fullKey, value: JSON.stringify(val) });
            } else {
                lines.push(...formatLines(val, fullKey));
            }
        }
        return lines;
    }
</script>

{#if items.length === 0}
    <p class="text-muted">No items selected.</p>
{:else}
    <div class="item-list">
        {#each items as item}
            <div class="item-block">
                <h5 class="item-title">{item.title}</h5>
                <div class="lines">
                    {#each formatLines(item.content) as line}
                        <div class="line">
                            <span class="key">{line.label}</span>
                            <span class="sep">:</span>
                            <span class="val">{line.value}</span>
                        </div>
                    {/each}
                </div>
            </div>
        {/each}
    </div>
{/if}

<style>
    .item-list {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .item-block {
        background: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 12px;
    }
    .item-title {
        margin: 0 0 8px 0;
        font-size: 0.95em;
        color: #333;
        border-bottom: 1px solid #eee;
        padding-bottom: 6px;
    }
    .lines {
        font-family: monospace;
        font-size: 0.85em;
        line-height: 1.5;
    }
    .line {
        display: flex;
        gap: 4px;
    }
    .key {
        color: #888;
        white-space: nowrap;
    }
    .sep {
        color: #bbb;
    }
    .val {
        color: #333;
        word-break: break-all;
    }
</style>
