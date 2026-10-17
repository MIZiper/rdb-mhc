<script lang="ts">
    import type { ViewerProps } from "../registry";
    import Stack from "../../components/ui/Stack.svelte";

    let { content_in }: ViewerProps = $props();
</script>

<Stack gap={2}>
    <span>Data (read-only)</span>
    <pre class="bg-body-tertiary p-3 rounded overflow-auto mb-0">{JSON.stringify(
        content_in,
        null,
        2,
    )}</pre>
</Stack>
