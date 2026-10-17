<script lang="ts">
    import { Button, Input } from "@sveltestrap/sveltestrap";
    import Stack from "../../components/ui/Stack.svelte";

    let jsonText: string = $state("{}");
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
