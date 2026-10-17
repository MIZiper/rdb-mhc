<script lang="ts">
    import { Card, CardBody, CardTitle } from "@sveltestrap/sveltestrap";
    import type { TypeViewerProps } from "../registry";
    import Stack from "../../components/ui/Stack.svelte";

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
    <Stack gap={3}>
        {#each items as item}
            <Card>
                <CardBody>
                    <CardTitle class="h6 border-bottom pb-2 mb-2">{item.title}</CardTitle>
                    <div class="font-monospace small">
                        {#each formatLines(item.content) as line}
                            <div class="d-flex gap-1">
                                <span class="text-secondary text-nowrap">{line.label}</span>
                                <span class="text-secondary">:</span>
                                <span class="text-break">{line.value}</span>
                            </div>
                        {/each}
                    </div>
                </CardBody>
            </Card>
        {/each}
    </Stack>
{/if}
