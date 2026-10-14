import type { FieldKey, TypeDescriptor } from "../../types";
import { request } from "./client";

let typesCache: TypeDescriptor[] | null = null;

/** Fetch all registered content-type descriptors (cached). */
export async function fetchTypes(force = false): Promise<TypeDescriptor[]> {
    if (typesCache && !force) return typesCache;
    try {
        const res = await fetch("/api/types");
        if (!res.ok) return (typesCache = []);
        typesCache = (await res.json()) as TypeDescriptor[];
        return typesCache;
    } catch {
        return (typesCache = []);
    }
}

export async function fetchType(type: string): Promise<TypeDescriptor | null> {
    try {
        return await request<TypeDescriptor>(`/api/types/${encodeURIComponent(type)}`);
    } catch {
        return null;
    }
}

export async function fetchFieldKeys(): Promise<FieldKey[]> {
    try {
        return await request<FieldKey[]>("/api/nodes/fields");
    } catch {
        return [];
    }
}

export interface FieldValueFacet {
    value: string;
    count: number;
}

export interface FieldValues {
    key: string;
    kind: string;
    values?: FieldValueFacet[];
    count?: number;
    min?: number | null;
    max?: number | null;
}

export async function fetchFieldValues(
    key: string,
    limit = 50,
): Promise<FieldValues | null> {
    try {
        return await request<FieldValues>(
            `/api/nodes/fields/${encodeURIComponent(key)}/values?limit=${limit}`,
        );
    } catch {
        return null;
    }
}
