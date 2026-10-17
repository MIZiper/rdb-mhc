<script lang="ts">
    import type { ViewerProps } from "../registry";
    import {
        imageFullUrl,
        imageThumbUrl,
        parseImageGallery,
        type ImageGalleryContent,
    } from "../../lib/utils/image";
    import ImageLightbox from "../../components/ImageLightbox.svelte";
    import ImageTile from "../../components/ui/ImageTile.svelte";

    let { content_in }: ViewerProps = $props();

    let gallery: ImageGalleryContent | null = $derived(parseImageGallery(content_in));
    let images = $derived(gallery?.images ?? []);

    let lightboxIndex: number | null = $state(null);

    let lightboxImages = $derived(
        images.map((img) => ({ src: imageFullUrl(img.file_id), caption: img.caption })),
    );
</script>

{#if images.length === 0}
    <p class="text-muted">No images</p>
{:else}
    <div class="row g-3">
        {#each images as img, i (img.file_id + i)}
            <div class="col-6 col-md-4 col-lg-3">
                <ImageTile
                    src={imageThumbUrl(img.file_id)}
                    alt={img.caption || ""}
                    caption={img.caption || ""}
                    onclick={() => (lightboxIndex = i)}
                />
            </div>
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
