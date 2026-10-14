import type { TagMeta } from "@mizip/metahub";

export type { TagMeta };

/** A node as shown in lists. */
export interface ItemMeta {
    id: string | null;
    title: string;
    description: string;
    update_time: Date;
    tags: TagMeta[];
    data_type: string | null;
    creator_name: string | null;
    creator_sub: string | null;
    status: string;
    visibility: string;
    /** Projected preview fields (keyed by canonical field key). */
    fields?: Record<string, unknown>;
}

/** A node with its full content, as shown in the detail view. */
export interface ItemDetail extends ItemMeta {
    content: any;
}

// --- Content-type descriptors ---------------------------------------------

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

// --- Query / aggregation ---------------------------------------------------

export type FilterOp = "eq" | "ne" | "gt" | "gte" | "lt" | "lte" | "contains";
export type TagMode = "exact" | "ancestors";
export type AggFunc = "count" | "avg" | "min" | "max" | "sum";

export interface QueryFilter {
    key: string;
    op: FilterOp;
    value: any;
}

export interface NodeQuery {
    text?: string;
    types?: string[];
    tag_ids?: number[];
    tag_mode?: TagMode;
    filters?: QueryFilter[];
    status?: string;
    page?: number;
    page_size?: number;
}

export interface NodeQueryResult {
    items: any[];
    total: number;
}

export interface AggregateRequest {
    types?: string[];
    tag_ids?: number[];
    tag_mode?: TagMode;
    filters?: QueryFilter[];
    status?: string;
    group_by?: string[];
    group_by_tag?: boolean;
    metric?: string | null;
    func?: AggFunc;
}

export interface AggregateGroup {
    group: Record<string, any>;
    value: number | null;
    count: number;
    sample_size: number;
}

export interface AggregateResult {
    groups: AggregateGroup[];
    total_nodes: number;
}
