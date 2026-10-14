import type { ItemMeta } from "../types";
import { constructTagsById, fetchTagsInfo } from "./api/metahub";

export interface NodePage {
    items: any[];
    total: number;
}

/**
 * Shared list state + loading for node pages: fetches a page of raw node
 * metadata, resolves tags and maps everything to ``ItemMeta``.
 */
export function useNodeList(metahubHost: string, pageSize = 10) {
    let items = $state<ItemMeta[]>([]);
    let total = $state(0);
    let loading = $state(false);
    let error = $state<string | null>(null);
    let page = $state(1);

    let totalPages = $derived(Math.max(1, Math.ceil(total / pageSize)));

    async function toItems(rawItems: any[]): Promise<ItemMeta[]> {
        const uniqueTagIds = [
            ...new Set(rawItems.flatMap((item) => item.tag_ids)),
        ] as number[];
        const cache = await fetchTagsInfo(metahubHost, uniqueTagIds);
        return rawItems.map((e) => ({
            id: e.id,
            title: e.title,
            description: e.description,
            update_time: new Date(e.updated_at),
            tags: constructTagsById(e.tag_ids, cache),
            data_type: e.data_type,
            creator_name: e.creator_name,
            creator_sub: e.creator_sub,
            status: e.status,
            visibility: e.visibility || "public",
            fields: e.fields || {},
        }));
    }

    async function load(
        loader: () => Promise<NodePage>,
        targetPage: number = page,
    ): Promise<void> {
        page = targetPage;
        loading = true;
        error = null;
        try {
            const data = await loader();
            items = await toItems(data.items);
            total = data.total ?? items.length;
        } catch (e: any) {
            error = e.message || "Failed to load";
        } finally {
            loading = false;
        }
    }

    return {
        get items() {
            return items;
        },
        get total() {
            return total;
        },
        get loading() {
            return loading;
        },
        get error() {
            return error;
        },
        get page() {
            return page;
        },
        get pageSize() {
            return pageSize;
        },
        get totalPages() {
            return totalPages;
        },
        load,
    };
}
