<script lang="ts">
    import { onDestroy } from "svelte";
    import type { EditorProps } from "../lib/processor";
    import { deleteImage, uploadImage } from "../lib/imageStore";
    import { imageThumbUrl } from "../lib/imageGallery";
    import AuthImage from "./AuthImage.svelte";

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

<div id="main">
    <div
        class="dropzone"
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
        <p>拖拽图片到此处，或</p>
        <label class="file-btn">
            选择图片
            <input type="file" accept="image/*" multiple onchange={onFileInput} />
        </label>
        <p class="hint">支持多张图片；原始文件会上传保存并自动生成缩略图。</p>
    </div>

    {#if images.length === 0}
        <p class="text-muted">尚未添加图片</p>
    {:else}
        <div class="grid">
            {#each images as img (img.key)}
                <div class="card" class:error={img.status === "error"}>
                    <div class="thumb">
                        {#if img.localUrl}
                            <img src={img.localUrl} alt={img.caption || img.original_name || ""} />
                        {:else if img.file_id}
                            <AuthImage src={imageThumbUrl(img.file_id)} alt={img.caption || ""} />
                        {/if}
                        {#if img.status === "uploading"}
                            <div class="overlay">上传中…</div>
                        {:else if img.status === "error"}
                            <div class="overlay err" title={img.error}>上传失败</div>
                        {/if}
                    </div>
                    <input
                        class="caption"
                        type="text"
                        placeholder="图片说明"
                        value={img.caption}
                        oninput={(e: Event) => setCaption(img.key, (e.target as HTMLInputElement).value)}
                    />
                    <div class="card-actions">
                        <button
                            class="mini"
                            title="上移"
                            disabled={images.indexOf(img) === 0}
                            onclick={() => moveImage(img.key, -1)}
                        >↑</button>
                        <button
                            class="mini"
                            title="下移"
                            disabled={images.indexOf(img) === images.length - 1}
                            onclick={() => moveImage(img.key, 1)}
                        >↓</button>
                        <button class="mini del" title="删除" onclick={() => removeImage(img.key)}>×</button>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    #main {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .dropzone {
        border: 2px dashed #c7cfcf;
        border-radius: 8px;
        padding: 18px;
        text-align: center;
        background: #fafcfc;
        transition: background 0.15s, border-color 0.15s;
    }
    .dropzone.active {
        border-color: #49a9a7;
        background: #eef7f6;
    }
    .dropzone p {
        margin: 4px 0;
        color: #666;
        font-size: 0.9em;
    }
    .hint {
        font-size: 0.78em !important;
        color: #999 !important;
    }
    .file-btn {
        display: inline-block;
        border: 1px solid #49a9a7;
        color: #2b7b79;
        background: #fff;
        border-radius: 4px;
        padding: 4px 14px;
        cursor: pointer;
        font-size: 0.88em;
    }
    .file-btn input {
        display: none;
    }
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 12px;
    }
    .card {
        border: 1px solid #e2e2e2;
        border-radius: 6px;
        padding: 8px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        background: #fafafa;
    }
    .card.error {
        border-color: #e0b4b4;
    }
    .thumb {
        position: relative;
        aspect-ratio: 4 / 3;
        background: #eef1f1;
        border-radius: 4px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .overlay {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.75);
        font-size: 0.82em;
        color: #555;
    }
    .overlay.err {
        color: #b00020;
        background: rgba(255, 235, 235, 0.85);
    }
    .caption {
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 3px 6px;
        font-size: 0.85em;
    }
    .card-actions {
        display: flex;
        gap: 6px;
    }
    .mini {
        border: 1px solid #ccc;
        border-radius: 3px;
        background: #fff;
        cursor: pointer;
        font-size: 0.85em;
        padding: 1px 8px;
    }
    .mini:disabled {
        opacity: 0.4;
        cursor: default;
    }
    .mini.del {
        color: #c00;
        margin-left: auto;
    }
</style>
