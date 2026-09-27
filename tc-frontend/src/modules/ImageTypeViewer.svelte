<script lang="ts">
    import { Col, Row } from "@sveltestrap/sveltestrap";
    import type { TypeViewerProps } from "../lib/processor";
    import {
        imageFullUrl,
        imageThumbUrl,
        parseImageGallery,
        type ImageEntry,
    } from "../lib/imageGallery";
    import AuthImage from "./AuthImage.svelte";
    import ImageLightbox from "./ImageLightbox.svelte";

    interface ItemGallery {
        key: string;
        title: string;
        images: ImageEntry[];
    }

    let { items }: TypeViewerProps = $props();

    let galleries: ItemGallery[] = $derived.by(() => {
        const out: ItemGallery[] = [];
        items.forEach((it, i) => {
            const content = parseImageGallery(it.content);
            if (content && content.images.length > 0) {
                out.push({ key: `${i}:${it.title}`, title: it.title, images: content.images });
            }
        });
        return out;
    });

    let selected: Set<string> = $state(new Set());
    let initialized: boolean = $state(false);

    $effect(() => {
        if (!initialized && galleries.length > 0) {
            selected = new Set(galleries.map((g) => g.key));
            initialized = true;
        }
    });

    function toggle(key: string) {
        const next = new Set(selected);
        if (next.has(key)) next.delete(key);
        else next.add(key);
        selected = next;
    }

    let displayed = $derived(galleries.filter((g) => selected.has(g.key)));

    let sections = $derived.by(() => {
        let offset = 0;
        return displayed.map((g) => {
            const start = offset;
            offset += g.images.length;
            return { key: g.key, title: g.title, images: g.images, start };
        });
    });

    let flatImages = $derived(
        displayed.flatMap((g) =>
            g.images.map((img) => ({
                src: imageFullUrl(img.file_id),
                caption: img.caption,
                itemTitle: g.title,
            })),
        ),
    );

    let lightboxIndex: number | null = $state(null);
</script>

{#if galleries.length === 0}
    <p class="text-muted">No valid Image data in selected items.</p>
{:else}
    <Row>
        <Col xs="3">
            <div class="sidebar">
                <h6>资源选择</h6>
                <div class="toggle-row">
                    <button class="mini" onclick={() => (selected = new Set(galleries.map((g) => g.key)))}>全选</button>
                    <button class="mini" onclick={() => (selected = new Set())}>清空</button>
                </div>
                <div class="checkbox-list">
                    {#each galleries as g (g.key)}
                        <label class="check-item">
                            <input type="checkbox" checked={selected.has(g.key)} onchange={() => toggle(g.key)} />
                            <span>
                                <span class="item-title">{g.title}</span>
                                <span class="count">{g.images.length} 张</span>
                            </span>
                        </label>
                    {/each}
                </div>
            </div>
        </Col>
        <Col xs="9">
            <div class="main-area">
                {#if displayed.length === 0}
                    <p class="text-muted">请选择要显示的图片资源。</p>
                {:else}
                    {#each sections as section (section.key)}
                        <div class="section">
                            <h6 class="section-title">{section.title}</h6>
                            <div class="gallery">
                                {#each section.images as img, i (`${section.key}-${img.file_id}-${i}`)}
                                    <button
                                        type="button"
                                        class="tile"
                                        onclick={() => (lightboxIndex = section.start + i)}
                                    >
                                        <span class="thumb">
                                            <AuthImage src={imageThumbUrl(img.file_id)} alt={img.caption || ""} />
                                        </span>
                                        {#if img.caption}
                                            <span class="caption">{img.caption}</span>
                                        {/if}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {/each}
                {/if}
            </div>
        </Col>
    </Row>
{/if}

{#if lightboxIndex !== null}
    <ImageLightbox
        images={flatImages}
        index={lightboxIndex}
        onclose={() => (lightboxIndex = null)}
        onindex={(i) => (lightboxIndex = i)}
    />
{/if}

<style>
    .sidebar {
        background: #f7f7f8;
        border-radius: 6px;
        padding: 12px;
    }
    .sidebar h6 {
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 0.85em;
        color: #555;
        border-bottom: 1px solid #ddd;
        padding-bottom: 4px;
    }
    .toggle-row {
        display: flex;
        gap: 6px;
        margin-bottom: 8px;
    }
    .mini {
        border: 1px solid #ccc;
        border-radius: 3px;
        background: #fff;
        cursor: pointer;
        font-size: 0.78em;
        padding: 1px 8px;
    }
    .checkbox-list {
        display: flex;
        flex-direction: column;
        gap: 4px;
        max-height: 60vh;
        overflow-y: auto;
    }
    .check-item {
        font-size: 0.85em;
        cursor: pointer;
        display: flex;
        align-items: flex-start;
        gap: 6px;
    }
    .check-item input {
        margin-top: 2px;
        flex-shrink: 0;
    }
    .item-title {
        display: block;
        font-weight: 500;
    }
    .count {
        display: block;
        color: #888;
        font-size: 0.9em;
    }
    .main-area {
        min-height: 200px;
    }
    .section {
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 0.92em;
        color: #333;
        border-left: 3px solid #49a9a7;
        padding-left: 8px;
        margin: 0 0 10px 0;
    }
    .gallery {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
        gap: 12px;
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
        padding: 5px 8px;
        font-size: 0.82em;
        color: #555;
        border-top: 1px solid #f0f0f0;
    }
</style>
