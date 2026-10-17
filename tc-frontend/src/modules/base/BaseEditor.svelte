<script lang="ts">
    import { Button, Input } from "@sveltestrap/sveltestrap";
    import Stack from "../../components/ui/Stack.svelte";
    import { untrack } from "svelte";
    import type { EditorProps } from "../registry";

    let { initial }: EditorProps = $props();

    function formatInitial(value: Record<string, any> | null | undefined): string {
        try {
            return JSON.stringify(value ?? {}, null, 2);
        } catch {
            return "{}";
        }
    }

    let jsonText: string = $state(formatInitial(untrack(() => initial)));
    let error: string | null = $state(null);

    export function getContent() {
        return JSON.parse(jsonText);
    }

    function Test() {
        try {
            JSON.parse(jsonText);
            error = null;
        } catch (e) {
            error = (e as Error).message;
        }
    }
</script>

<Stack gap={2}>
    <span>Data (JSON)</span>
    <Input type="textarea" rows={12} class="font-monospace" bind:value={jsonText} />

    {#if error}
        <div class="text-danger small">{error}</div>
    {/if}

    <div class="d-flex gap-2">
        <Button size="sm" color="secondary" onclick={Test}>Test</Button>
    </div>
</Stack>
