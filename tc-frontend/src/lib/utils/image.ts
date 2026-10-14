import { authFetch } from "../auth";

export interface ImageEntry {
    file_id: string;
    caption: string;
    original_name?: string | null;
    mime_type?: string | null;
    width?: number | null;
    height?: number | null;
}

export interface ImageGalleryContent {
    type: "image_gallery";
    images: ImageEntry[];
}

export function imageThumbUrl(fileId: string): string {
    return `/api/files/${encodeURIComponent(fileId)}/thumb`;
}

export function imageFullUrl(fileId: string): string {
    return `/api/files/${encodeURIComponent(fileId)}`;
}

export function parseImageGallery(content: unknown): ImageGalleryContent | null {
    let value = content;
    if (typeof value === "string") {
        try {
            value = JSON.parse(value);
        } catch {
            return null;
        }
    }
    if (!value || typeof value !== "object") return null;
    const images = (value as { images?: unknown }).images;
    if (!Array.isArray(images)) return null;
    return {
        type: "image_gallery",
        images: images
            .filter((e): e is Record<string, unknown> => !!e && typeof e === "object")
            .map((e) => ({
                file_id: String(e.file_id ?? ""),
                caption: typeof e.caption === "string" ? e.caption : "",
                original_name: (e.original_name as string | null | undefined) ?? null,
                mime_type: (e.mime_type as string | null | undefined) ?? null,
                width: typeof e.width === "number" ? e.width : null,
                height: typeof e.height === "number" ? e.height : null,
            }))
            .filter((e) => e.file_id.length > 0),
    };
}

// Reference-counted object URLs for authenticated images. Each image URL is
// fetched once as a blob and revoked when the last consumer releases it.

interface BlobEntry {
    refs: number;
    objectUrl: string | null;
    promise: Promise<string>;
}

const blobCache = new Map<string, BlobEntry>();

export function acquireBlobUrl(src: string): Promise<string> {
    let entry = blobCache.get(src);
    if (!entry) {
        const created: BlobEntry = {
            refs: 0,
            objectUrl: null,
            promise: Promise.resolve(""),
        };
        created.promise = (async () => {
            const res = await authFetch(src);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const blob = await res.blob();
            const objectUrl = URL.createObjectURL(blob);
            if (blobCache.get(src) !== created) {
                URL.revokeObjectURL(objectUrl);
                throw new Error("cancelled");
            }
            created.objectUrl = objectUrl;
            return objectUrl;
        })();
        blobCache.set(src, created);
        entry = created;
    }
    entry.refs++;
    return entry.promise;
}

export function releaseBlobUrl(src: string): void {
    const entry = blobCache.get(src);
    if (!entry) return;
    entry.refs--;
    if (entry.refs <= 0) {
        blobCache.delete(src);
        if (entry.objectUrl) URL.revokeObjectURL(entry.objectUrl);
    }
}
