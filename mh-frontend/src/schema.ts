export interface Tag {
    id: number | null;
    name: string;
    category: Category;
    exposed: boolean;
};

export interface Category {
    id: number | null;
    name: string;
    client_id?: number;
};