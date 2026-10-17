<script lang="ts">
    import { onDestroy } from "svelte";
    import { Button, Card, CardBody } from "@sveltestrap/sveltestrap";
    import type { EditorProps } from "../registry";
    import Stack from "../../components/ui/Stack.svelte";
    import { deleteImage, uploadImage } from "../../lib/api/files";
    import { imageThumbUrl } from "../../lib/utils/image";
    import AuthImage from "../../components/AuthImage.svelte";

    interface EditImage {
        key: string;
        file_id: string | null;
        original_name: string | null;
        mime_type: string | null;
        width: number | null;
        height: number | null;
        caption: string;
        status: "ready" | "uploading" | "error";
        error?: string;
        localUrl: string | null;
    }

    let { initial }: EditorProps = $props();

    function loadInitial(): EditImage[] {
        const imgs = initial?.images;
        if (!Array.isArray(imgs)) return [];
        return imgs
            .filter((e: any) => e && typeof e.file_id === "string" && e.file_id)
            .map((e: any) => ({
                key: crypto.randomUUID(),
                file_id: e.file_id,
                original_name: e.original_name ?? null,
                mime_type: e.mime_type ?? null,
                width: typeof e.width === "number" ? e.width : null,
                height: typeof e.height === "number" ? e.height : null,
                caption: typeof e.caption === "string" ? e.caption : "",
                status: "ready" as const,
                localUrl: null,
            }));
    }

    let images: EditImage[] = $state(loadInitial());
    let dragActive: boolean = $state(false);

    const uploadedInSession = new Set<string>();
    const removedIds = new Set<string>();

    onDestroy(() => {
        for (const e of images) {
            if (e.localUrl) URL.revokeObjectURL(e.localUrl);
        }
    });

    async function addFiles(fileList: FileList | File[] | null) {
        if (!fileList) return;
        const files = Array.from(fileList).filter((f) => f.type.startsWith("image/"));
        for (const file of files) {
            const key = crypto.randomUUID();
            const localUrl = URL.createObjectURL(file);
            images = [
                ...images,
                {
                    key,
                    file_id: null,
                    original_name: file.name,
                    mime_type: file.type,
                    width: null,
                    height: null,
                    caption: "",
                    status: "uploading",
                    localUrl,
                },
            ];
            try {
                const up = await uploadImage(file);
                uploadedInSession.add(up.id);
                images = images.map((e) =>
                    e.key === key
                        ? {
                              ...e,
                              file_id: up.id,
                              original_name: up.original_name,
                              mime_type: up.mime_type,
                              width: up.width,
                              height: up.height,
                              status: "ready",
                          }
                        : e,
                );
            } catch (err: any) {
                images = images.map((e) =>
                    e.key === key ? { ...e, status: "error", error: err.message } : e,
                );
            }
        }
    }

    function onFileInput(e: Event) {
        const input = e.target as HTMLInputElement;
        addFiles(input.files);
        input.value = "";
    }

    function onDrop(e: DragEvent) {
        e.preventDefault();
        dragActive = false;
        addFiles(e.dataTransfer?.files ?? null);
    }

    function setCaption(key: string, caption: string) {
        images = images.map((e) => (e.key === key ? { ...e, caption } : e));
    }

    function removeImage(key: string) {
        const entry = images.find((e) => e.key === key);
        if (!entry) return;
        if (entry.localUrl) URL.revokeObjectURL(entry.localUrl);
        if (entry.file_id) {
            if (uploadedInSession.has(entry.file_id)) {
                uploadedInSession.delete(entry.file_id);
                deleteImage(entry.file_id);
            } else {
                removedIds.add(entry.file_id);
            }
        }
        images = images.filter((e) => e.key !== key);
    }

    function moveImage(key: string, dir: -1 | 1) {
        const idx = images.findIndex((e) => e.key === key);
        const target = idx + dir;
        if (idx < 0 || target < 0 || target >= images.length) return;
        const next = [...images];
        [next[idx], next[target]] = [next[target], next[idx]];
        images = next;
    }

    export function getContent() {
        return {
            type: "image_gallery",
            images: images
                .filter((e) => e.status === "ready" && e.file_id)
                .map((e) => ({
                    file_id: e.file_id,
                    caption: e.caption,
                    original_name: e.original_name,
                    mime_type: e.mime_type,
                    width: e.width,
                    height: e.height,
                })),
        };
    }

    export function getRemovedFileIds(): string[] {
        return [...removedIds];
    }
</script>

<Stack gap={3}>
    <div
        class="dropzone text-center p-3"
        class:active={dragActive}
        role="button"
        tabindex="0"
        ondragover={(e: DragEvent) => {
            e.preventDefault();
            dragActive = true;
        }}
        ondragleave={() => (dragActive = false)}
        ondrop={onDrop}
    >
        <p class="mb-2 text-secondary">Drag images here, or</p>
        <label class="btn btn-outline-primary btn-sm mb-2">
            Choose images
            <input class="d-none" type="file" accept="image/*" multiple onchange={onFileInput} />
        </label>
        <p class="small text-secondary mb-0">
            Supports multiple images; originals are uploaded and thumbnails generated automatically.
        </p>
    </div>

    {#if images.length === 0}
        <p class="text-muted mb-0">No images yet</p>
    {:else}
        <div class="row g-3">
            {#each images as img (img.key)}
                <div class="col-6 col-md-4 col-lg-3">
                    <Card class={img.status === "error" ? "border-danger" : ""}>
                        <CardBody class="p-2 d-flex flex-column gap-2">
                            <div class="thumb">
                                {#if img.localUrl}
                                    <img
                                        class="w-100 h-100 object-fit-cover"
                                        src={img.localUrl}
                                        alt={img.caption || img.original_name || ""}
                                    />
                                {:else if img.file_id}
                                    <AuthImage
                                        src={imageThumbUrl(img.file_id)}
                                        alt={img.caption || ""}
                                        className="w-100 h-100 object-fit-cover"
                                    />
                                {/if}
                                {#if img.status === "uploading"}
                                    <div class="overlay">Uploading…</div>
                                {:else if img.status === "error"}
                                    <div class="overlay err" title={img.error}>Upload failed</div>
                                {/if}
                            </div>
                            <input
                                class="form-control form-control-sm"
                                type="text"
                                placeholder="Caption"
                                value={img.caption}
                                oninput={(e: Event) => setCaption(img.key, (e.target as HTMLInputElement).value)}
                            />
                            <div class="d-flex gap-1">
                                <Button
                                    size="sm"
                                    color="outline-secondary"
                                    title="Move up"
                                    disabled={images.indexOf(img) === 0}
                                    onclick={() => moveImage(img.key, -1)}
                                >↑</Button>
                                <Button
                                    size="sm"
                                    color="outline-secondary"
                                    title="Move down"
                                    disabled={images.indexOf(img) === images.length - 1}
                                    onclick={() => moveImage(img.key, 1)}
                                >↓</Button>
                                <Button
                                    size="sm"
                                    color="link"
                                    class="text-danger ms-auto"
                                    title="Delete"
                                    onclick={() => removeImage(img.key)}
                                >×</Button>
                            </div>
                        </CardBody>
                    </Card>
                </div>
            {/each}
        </div>
    {/if}
</Stack>

<style>
    .dropzone {
        border: 2px dashed var(--bs-border-color);
        border-radius: var(--bs-border-radius-lg);
        background: var(--bs-tertiary-bg);
        transition: background 0.15s, border-color 0.15s;
    }
    .dropzone.active {
        border-color: var(--bs-primary);
        background: rgba(var(--bs-primary-rgb), 0.1);
    }
    .thumb {
        position: relative;
        aspect-ratio: 4 / 3;
        background: var(--bs-secondary-bg);
        border-radius: var(--bs-border-radius);
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .overlay {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(var(--bs-white-rgb), 0.75);
        font-size: 0.82em;
        color: var(--bs-secondary-color);
    }
    .overlay.err {
        color: var(--bs-danger);
        background: rgba(var(--bs-danger-rgb), 0.15);
    }
</style>
