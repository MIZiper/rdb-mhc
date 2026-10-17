<script lang="ts">
    interface LegendItem {
        label: string;
        color: string;
    }

    let {
        items,
        class: className = "",
    }: {
        items: LegendItem[];
        class?: string;
    } = $props();
</script>

<div class="d-flex flex-wrap gap-3 small {className}">
    {#each items as item}
        <span class="d-inline-flex align-items-center gap-1">
            <span class="legend-swatch rounded-1" style="background:{item.color}"></span>
            {item.label}
        </span>
    {/each}
</div>

<style>
    .legend-swatch {
        width: 12px;
        height: 12px;
        flex: 0 0 auto;
    }
</style>
