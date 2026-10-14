import { authFetch } from "./auth";

export type FieldKind = "text" | "number" | "keyword" | "date";

export interface FieldSpec {
    path: string;
    key: string;
    kind: FieldKind;
    unit: string | null;
    label: string | null;
    comparable: boolean;
}

export interface TypeDescriptor {
    type: string;
    display_name: string;
    version: number;
    schema: any;
    preview: string[];
    ui: { component?: string };
    fields: FieldSpec[];
}

export interface FieldKey {
    key: string;
    kind: FieldKind;
    unit: string | null;
    label: string | null;
    comparable: boolean;
}

let _typesCache: TypeDescriptor[] | null = null;

export async function fetchTypes(force = false): Promise<TypeDescriptor[]> {
    if (_typesCache && !force) return _typesCache;
    try {
        const res = await fetch("/api/types");
        if (!res.ok) return (_typesCache = []);
        _typesCache = (await res.json()) as TypeDescriptor[];
        return _typesCache;
    } catch {
        return (_typesCache = []);
    }
}

export async function fetchFieldKeys(): Promise<FieldKey[]> {
    try {
        const res = await authFetch("/api/nodes/fields");
        if (!res.ok) return [];
        return (await res.json()) as FieldKey[];
    } catch {
        return [];
    }
}

export interface QueryFilter {
    key: string;
    op: "eq" | "ne" | "gt" | "gte" | "lt" | "lte" | "contains";
    value: any;
}

export interface NodeQuery {
    text?: string;
    types?: string[];
    tag_ids?: number[];
    tag_mode?: "exact" | "ancestors";
    filters?: QueryFilter[];
    status?: string;
    page?: number;
    page_size?: number;
}

export interface NodeQueryResult {
    items: any[];
    total: number;
}

export async function queryNodes(body: NodeQuery): Promise<NodeQueryResult> {
    const res = await authFetch("/api/nodes/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("Query failed");
    return (await res.json()) as NodeQueryResult;
}

export interface AggregateRequest {
    types?: string[];
    tag_ids?: number[];
    tag_mode?: "exact" | "ancestors";
    filters?: QueryFilter[];
    status?: string;
    group_by?: string[];
    group_by_tag?: boolean;
    metric?: string | null;
    func?: "count" | "avg" | "min" | "max" | "sum";
}

export interface AggregateGroup {
    group: Record<string, any>;
    value: number | null;
    count: number;
    sample_size: number;
}

export async function aggregateNodes(
    body: AggregateRequest,
): Promise<{ groups: AggregateGroup[]; total_nodes: number }> {
    const res = await authFetch("/api/nodes/aggregate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("Aggregate failed");
    return await res.json();
}

export async function batchNodeData(
    ids: string[],
): Promise<{ items: any[] }> {
    if (ids.length === 0) return { items: [] };
    const res = await authFetch(
        `/api/nodes/data?ids=${encodeURIComponent(ids.join(","))}`,
    );
    if (!res.ok) throw new Error("Batch fetch failed");
    return await res.json();
}
