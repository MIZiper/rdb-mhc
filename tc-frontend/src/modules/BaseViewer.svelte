<script lang="ts">
    let { data = {} }: { data?: Record<string, any> } = $props();
</script>

<main>
    <label>Data (read-only)</label>
    <pre>{JSON.stringify(data, null, 2)}</pre>
</main>

<style>
    pre {
        background: #f7f7f8;
        padding: 12px;
        border-radius: 4px;
        overflow: auto;
    }
    main {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
</style>
