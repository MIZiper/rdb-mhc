export interface Tag {
    id: number | null;
    name: string;
    category: Category;
    exposed: boolean;
    parent_id?: number | null;
};

export interface Category {
    id: number | null;
    name: string;
    client_id?: number;
};