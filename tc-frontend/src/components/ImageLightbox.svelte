<script lang="ts">
    import AuthImage from "./AuthImage.svelte";

    interface LightboxImage {
        src: string;
        caption?: string;
        itemTitle?: string;
    }

    let {
        images,
        index,
        onclose,
        onindex,
    }: {
        images: LightboxImage[];
        index: number;
        onclose: () => void;
        onindex: (i: number) => void;
    } = $props();

    let current = $derived(images[index] ?? null);

    function prev() {
        if (index > 0) onindex(index - 1);
    }
    function next() {
        if (index < images.length - 1) onindex(index + 1);
    }

    function onKeydown(e: KeyboardEvent) {
        if (e.key === "Escape") onclose();
        else if (e.key === "ArrowLeft") prev();
        else if (e.key === "ArrowRight") next();
    }
</script>

<svelte:window onkeydown={onKeydown} />

<div class="overlay" role="button" tabindex="-1" onclick={onclose} onkeydown={() => {}}>
    <div class="dialog" role="presentation" onclick={(e: MouseEvent) => e.stopPropagation()}>
        {#if current}
            <AuthImage src={current.src} alt={current.caption || ""} className="full-image" />
            <div class="bar">
                <div class="caption">
                    {#if current.itemTitle}
                        <span class="item-title">{current.itemTitle}</span>
                    {/if}
                    {#if current.caption}
                        <span class="cap-text">{current.caption}</span>
                    {/if}
                </div>
                <div class="counter">{index + 1} / {images.length}</div>
            </div>
        {/if}
        <button class="close" title="Close (Esc)" onclick={onclose}>×</button>
        {#if index > 0}
            <button class="nav prev" title="Previous (←)" onclick={prev}>‹</button>
        {/if}
        {#if index < images.length - 1}
            <button class="nav next" title="Next (→)" onclick={next}>›</button>
        {/if}
    </div>
</div>

<style>
    .overlay {
        position: fixed;
        inset: 0;
        background: rgba(var(--bs-black-rgb), 0.82);
        z-index: 2000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
        cursor: zoom-out;
    }
    .dialog {
        position: relative;
        max-width: 92vw;
        max-height: 92vh;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        cursor: default;
    }
    :global(.full-image) {
        max-width: 92vw;
        max-height: 80vh;
        object-fit: contain;
        margin: 0 auto;
        border-radius: var(--bs-border-radius);
        background: var(--bs-black);
    }
    .bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        color: var(--bs-white);
        font-size: 0.9em;
    }
    .caption {
        display: flex;
        flex-direction: column;
    }
    .item-title {
        font-size: 0.8em;
        color: var(--bs-primary);
    }
    .cap-text {
        color: var(--bs-white);
    }
    .counter {
        color: var(--bs-secondary-color);
        white-space: nowrap;
    }
    .close {
        position: absolute;
        top: -34px;
        right: 0;
        border: none;
        background: none;
        color: var(--bs-white);
        font-size: 2em;
        line-height: 1;
        cursor: pointer;
        padding: 0 6px;
    }
    .nav {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        border: none;
        background: rgba(var(--bs-white-rgb), 0.12);
        color: var(--bs-white);
        font-size: 2.4em;
        line-height: 1;
        width: 48px;
        height: 72px;
        cursor: pointer;
        border-radius: var(--bs-border-radius-lg);
    }
    .nav:hover {
        background: rgba(var(--bs-white-rgb), 0.25);
    }
    .prev {
        left: -60px;
    }
    .next {
        right: -60px;
    }
    @media (max-width: 720px) {
        .prev {
            left: 4px;
        }
        .next {
            right: 4px;
        }
    }
</style>
