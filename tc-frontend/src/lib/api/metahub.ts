import type { TagMeta } from "../../types";

type TagsCache = Record<number, Record<string, any>>;

/** Resolve tag ids to tag metadata via MetaHub. */
export async function fetchTagsInfo(
    mhHost: string = "",
    allTagIds: number[],
): Promise<TagsCache> {
    if (allTagIds.length === 0) return {};
    try {
        const res = await fetch(`${mhHost}/api/tags/resolve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(allTagIds),
        });
        if (!res.ok) return {};
        const data: Record<string, any>[] = await res.json();
        return Object.fromEntries(data.map((item) => [item.id, item]));
    } catch {
        return {};
    }
}

export function constructTagsById(
    tagIds: number[],
    cache: TagsCache,
): TagMeta[] {
    return tagIds.map((id) => ({
        id,
        name: cache[id]?.name ?? `@${id}`,
    }));
}
