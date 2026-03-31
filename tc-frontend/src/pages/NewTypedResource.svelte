<script lang="ts">
    import { BaseProcessor, registry } from "../lib/processor";

    let selected: string | null = $state(null);
    let processor: BaseProcessor | null = $state(null);

    $effect(() => {
        if (selected) processor = registry.getProcessor(selected);
    });
</script>

<div>
    <select bind:value={selected}>
        {#each registry.allProcessors() as { type: type_id, name }}
            <option value={type_id}>{name}</option>
        {/each}
    </select>

    {#if processor}
        <processor.editor />
    {/if}
</div>
