import type { TagMeta } from "../schema";

export async function fetch_tags_info(
    mh_host: string = "",
    all_tag_ids: number[],
): Promise<Record<number, Record<string, any>>> {
    // make this exportable
    if (all_tag_ids.length === 0) return [];
    const res = await fetch(`${mh_host}/api/tags/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(all_tag_ids),
    });
    if (!res.ok) throw Error("Failed to get data.");
    const data: Record<string, any>[] = await res.json();
    return Object.fromEntries(data.map((itm) => [itm.id, itm]));
}

export function construct_tags_by_ids(tag_ids: number[], tags_cache: Record<number, Record<string, any>>): TagMeta[] {
    return tag_ids.map((e) => ({
        id: e,
        name: tags_cache[e].name,
    }));
}