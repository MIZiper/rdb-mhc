import { authFetch } from "../auth";

/** Authenticated JSON request; throws on non-2xx responses. */
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await authFetch(path, init);
    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error((detail as any)?.detail || `Request failed (${res.status})`);
    }
    return (await res.json()) as T;
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
    return request<T>(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}
