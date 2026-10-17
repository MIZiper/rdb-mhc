<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardHeader,
        Col,
        Row,
    } from "@sveltestrap/sveltestrap";
    import type { TypeViewerProps } from "../registry";
    import {
        imageFullUrl,
        imageThumbUrl,
        parseImageGallery,
        type ImageEntry,
    } from "../../lib/utils/image";
    import ImageLightbox from "../../components/ImageLightbox.svelte";
    import ImageTile from "../../components/ui/ImageTile.svelte";

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
    <Row class="g-3">
        <Col xs="3">
            <Card>
                <CardHeader class="py-2 fw-semibold">Select resources</CardHeader>
                <CardBody class="pt-2">
                    <div class="d-flex gap-2 mb-2">
                        <Button size="sm" color="outline-secondary" onclick={() => (selected = new Set(galleries.map((g) => g.key)))}>Select all</Button>
                        <Button size="sm" color="outline-secondary" onclick={() => (selected = new Set())}>Clear</Button>
                    </div>
                    <div class="checkbox-list">
                        {#each galleries as g (g.key)}
                            <label class="form-check mb-1">
                                <input
                                    class="form-check-input mt-1"
                                    type="checkbox"
                                    checked={selected.has(g.key)}
                                    onchange={() => toggle(g.key)}
                                />
                                <span class="form-check-label">
                                    <span class="d-block fw-medium">{g.title}</span>
                                    <span class="d-block small text-secondary">{g.images.length} images</span>
                                </span>
                            </label>
                        {/each}
                    </div>
                </CardBody>
            </Card>
        </Col>
        <Col xs="9">
            <div class="main-area">
                {#if displayed.length === 0}
                    <p class="text-muted">Select image resources to display.</p>
                {:else}
                    {#each sections as section (section.key)}
                        <div class="mb-3">
                            <h6 class="border-start border-3 ps-2 mb-2">{section.title}</h6>
                            <div class="row g-3">
                                {#each section.images as img, i (`${section.key}-${img.file_id}-${i}`)}
                                    <div class="col-6 col-md-4">
                                        <ImageTile
                                            src={imageThumbUrl(img.file_id)}
                                            alt={img.caption || ""}
                                            caption={img.caption || ""}
                                            onclick={() => (lightboxIndex = section.start + i)}
                                        />
                                    </div>
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
    .checkbox-list {
        max-height: 60vh;
        overflow-y: auto;
    }
    .main-area {
        min-height: 200px;
    }
</style>
