import { authFetch } from "../auth";

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

export async function uploadImage(
    file: File,
    dataType = "Image.v00",
): Promise<UploadedImage> {
    const form = new FormData();
    form.append("file", file);
    const res = await authFetch(
        `/api/files?data_type=${encodeURIComponent(dataType)}`,
        { method: "POST", body: form },
    );
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as any)?.detail || `Upload failed (${res.status})`);
    }
    return res.json();
}

export async function deleteImage(fileId: string): Promise<void> {
    try {
        await authFetch(`/api/files/${encodeURIComponent(fileId)}`, {
            method: "DELETE",
        });
    } catch {
        // Best effort; orphan cleanup can happen later.
    }
}
