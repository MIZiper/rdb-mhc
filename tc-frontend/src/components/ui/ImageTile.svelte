<script lang="ts">
    import AuthImage from "../AuthImage.svelte";

    let {
        src,
        alt = "",
        caption = "",
        onclick,
        class: className = "",
    }: {
        src: string;
        alt?: string;
        caption?: string;
        onclick?: (event: MouseEvent) => void;
        class?: string;
    } = $props();
</script>

<button type="button" class="card tile {className}" {onclick}>
    <span class="ratio ratio-4x3 bg-body-secondary overflow-hidden">
        <AuthImage {src} {alt} className="w-100 h-100 object-fit-cover" />
    </span>
    {#if caption}
        <span class="card-body py-1 px-2 small text-secondary text-truncate">{caption}</span>
    {/if}
</button>

<style>
    .tile {
        display: block;
        width: 100%;
        padding: 0;
        color: inherit;
        font: inherit;
        text-align: left;
        overflow: hidden;
        cursor: zoom-in;
    }
    .tile:hover {
        box-shadow: var(--bs-box-shadow-sm);
    }
</style>
