<script lang="ts">
    let jsonText: string = $state("{}");
    let error: string | null = $state(null);

    export function getContent() {
        return JSON.parse(jsonText);
    }

    function Test() {
        try {
            const parsed = JSON.parse(jsonText);
            error = null;
        } catch (e) {
            error = (e as Error).message;
        }
    }
</script>

<div id="main">
    <span>Data (JSON)</span>
    <textarea bind:value={jsonText} rows="12"></textarea>

    {#if error}
        <div class="error">{error}</div>
    {/if}

    <div class="actions">
        <button onclick={Test}>Test</button>
    </div>
</div>

<style>
    #main {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    textarea {
        font-family: monospace;
        width: 100%;
        box-sizing: border-box;
    }
    .actions {
        display: flex;
        gap: 8px;
    }
    .error {
        color: #b00020;
        font-size: 0.9em;
    }
</style>
