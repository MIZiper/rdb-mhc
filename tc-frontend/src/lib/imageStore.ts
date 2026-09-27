import { authFetch } from "./auth";

export interface UploadedImage {
    id: string;
    node_id?: string | null;
    data_type: string;
    original_name: string | null;
    mime_type: string;
    size_bytes: number;
    width: number | null;
    height: number | null;
    url: string;
    thumb_url: string;
}

export async function uploadImage(file: File, dataType = "Image.v00"): Promise<UploadedImage> {
    const form = new FormData();
    form.append("file", file);
    const res = await authFetch(`/api/files?data_type=${encodeURIComponent(dataType)}`, {
        method: "POST",
        body: form,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Upload failed (${res.status})`);
    }
    return res.json();
}

export async function deleteImage(fileId: string): Promise<void> {
    try {
        await authFetch(`/api/files/${encodeURIComponent(fileId)}`, { method: "DELETE" });
    } catch {
        // best effort; orphan cleanup can be done later
    }
}

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
