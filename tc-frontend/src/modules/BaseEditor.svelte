<script lang="ts">
    let {
        data = {},
        OnSave = null,
        OnCancel,
    }: {
        data?: Record<string, any>;
        OnSave: ((data: any) => void) | null;
        OnCancel: (() => void) | null;
    } = $props();

    let jsonText: string = $state("");
    let error: string | null = $state(null);

    $effect(() => {
        // keep the editor in sync when incoming `data` changes
        jsonText = JSON.stringify(data, null, 2);
    });

    function onSave() {
        try {
            const parsed = JSON.parse(jsonText);
            error = null;
            if (OnSave) OnSave(parsed);
        } catch (e) {
            error = (e as Error).message;
        }
    }

    function onCancel() {
        if (OnCancel) OnCancel();
    }
</script>

<main>
    <label>Data (JSON)</label>
    <textarea bind:value={jsonText} rows="12" />

    {#if error}
        <div class="error">{error}</div>
    {/if}

    <div class="actions">
        <button onclick={onSave}>Save</button>
        <button type="button" onclick={onCancel}>Cancel</button>
    </div>
</main>

<style>
    main {
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
