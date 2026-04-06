<script lang="ts">
    import type { ViewerProps } from "../lib/processor";

    let { content_in }: ViewerProps = $props();
</script>

<div id="main">
    <span>Data (read-only)</span>
    <pre>{JSON.stringify(content_in, null, 2)}</pre>
</div>

<style>
    pre {
        background: #f7f7f8;
        padding: 12px;
        border-radius: 4px;
        overflow: auto;
    }
    #main {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
</style>
