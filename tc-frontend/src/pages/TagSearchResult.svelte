<script lang="ts">
    import { Container, ListGroup } from "@sveltestrap/sveltestrap";
    import ResourceItem from "../lib/ResourceItem.svelte";
    import type { ItemMeta } from "../schema";

    import { getContext, onMount } from "svelte";
    import { construct_tags_by_ids, fetch_tags_info } from "./FetchMetaHubTags";

    let router: any = getContext("router");
    let items: ItemMeta[] = $state([]);
    let loading = $state(false);

    let totalItems = $state(0);
    let metahub_host = (getContext("mh_host") as string) || "";

    async function loadData(tag_ids: number[]) {
        loading = true;

        const res = await fetch(`/api/nodes/by_tags`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tag_ids),
        });
        if (!res.ok) return;
        const data = await res.json();

        const uniqueTagIds = [
            ...new Set(data.items.flatMap((item: any) => item.tag_ids)),
        ] as number[];

        const tags_cache = await fetch_tags_info(metahub_host, uniqueTagIds);

        items = data.items.map((e: any) => ({
            id: e.id,
            title: e.title,
            description: e.description,
            update_time: new Date(e.updated_at),
            tags: construct_tags_by_ids(e.tag_ids, tags_cache),
        }));
        totalItems = data.total || 0;

        loading = false;
    }

    $effect(() => {
        const tag_id_str = router.route.getParams(
            "/tags/:tag_id/:tag_str",
        ).tag_id;
        loadData([Number(tag_id_str)]).then(() => {});
    });
</script>

<Container class="my-2" fluid>
    {#if loading}
        <p>Loading</p>
    {:else}
        <p class="meta">
            Top {totalItems} items displayed.
        </p>

        <ListGroup class="mt-2">
            {#each items as item}
                <ResourceItem {item} />
            {/each}
        </ListGroup>
    {/if}
</Container>
