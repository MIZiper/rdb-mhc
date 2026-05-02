export interface TagMeta {
    id: number | null;
    name: string;
    parent_id?: number | null;
}

export interface TagDetail extends TagMeta {
    category_id: number;
    exposed: boolean;
};

export interface Category {
    id: number | null;
    name: string;
    client_id?: number;
};

export interface Client {
    id: number | null;
    name: string;
    host: string | null;
};

export interface NodeRegistration {
    tag_id: number;
    client_id: number;
    client_node_id: string;
    node_tag_ids: number[];
    params: Record<string, unknown>;
};

export interface NodeRegistrationList {
    items: NodeRegistration[];
    total: number;
};

export interface TagDescendant {
    id: number;
    name: string;
    parent_id: number | null;
};