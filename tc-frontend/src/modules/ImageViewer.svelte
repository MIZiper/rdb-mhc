<script lang="ts">
    import type { ViewerProps } from "../lib/processor";
    import {
        imageFullUrl,
        imageThumbUrl,
        parseImageGallery,
        type ImageGalleryContent,
    } from "../lib/imageGallery";
    import AuthImage from "./AuthImage.svelte";
    import ImageLightbox from "./ImageLightbox.svelte";

    let { content_in }: ViewerProps = $props();

    let gallery: ImageGalleryContent | null = $derived(parseImageGallery(content_in));
    let images = $derived(gallery?.images ?? []);

    let lightboxIndex: number | null = $state(null);

    let lightboxImages = $derived(
        images.map((img) => ({ src: imageFullUrl(img.file_id), caption: img.caption })),
    );
</script>

{#if images.length === 0}
    <p class="text-muted">无图片</p>
{:else}
    <div class="gallery">
        {#each images as img, i (img.file_id + i)}
            <button type="button" class="tile" onclick={() => (lightboxIndex = i)}>
                <span class="thumb">
                    <AuthImage src={imageThumbUrl(img.file_id)} alt={img.caption || ""} />
                </span>
                {#if img.caption}
                    <span class="caption">{img.caption}</span>
                {/if}
            </button>
        {/each}
    </div>
{/if}

{#if lightboxIndex !== null}
    <ImageLightbox
        images={lightboxImages}
        index={lightboxIndex}
        onclose={() => (lightboxIndex = null)}
        onindex={(i) => (lightboxIndex = i)}
    />
{/if}

<style>
    .gallery {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 14px;
    }
    .tile {
        display: block;
        width: 100%;
        padding: 0;
        color: inherit;
        font: inherit;
        text-align: left;
        border: 1px solid #e6e6e6;
        border-radius: 6px;
        overflow: hidden;
        background: #fff;
        cursor: zoom-in;
        transition: box-shadow 0.15s;
    }
    .tile:hover {
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
    }
    .thumb {
        display: flex;
        aspect-ratio: 4 / 3;
        align-items: center;
        justify-content: center;
        background: #f2f4f4;
        overflow: hidden;
    }
    .thumb :global(img) {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .caption {
        display: block;
        padding: 6px 8px;
        font-size: 0.84em;
        color: #555;
        border-top: 1px solid #f0f0f0;
    }
</style>
