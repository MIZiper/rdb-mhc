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