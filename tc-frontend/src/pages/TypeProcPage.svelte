<script lang="ts">
    import {
        Button,
        ButtonGroup,
        Col,
        Container,
        ListGroup,
        Pagination,
        PaginationItem,
        PaginationLink,
        Row,
        Spinner,
    } from "@sveltestrap/sveltestrap";
    import ResourceItem from "../lib/ResourceItem.svelte";
    import type { ItemMeta } from "../schema";
    import { getContext } from "svelte";
    import { fetch_tags_info, construct_tags_by_ids } from "./FetchMetaHubTags";
    import { searchParams } from "sv-router";

    let router: any = getContext("router");
    const type_name = router.route.getParams("/types/:type_name").type_name;

    let items: ItemMeta[] = $state([]);
    let loading: boolean = $state(true);
    let error: string | null = $state(null);

    const pageSize = 10;
    let currentPage = $state(1);
    let totalItems = $state(0);
    let totalPages = $derived(Math.ceil(totalItems / pageSize));
    let metahub_host = (getContext("mh_host") as string) || "";

    const RANGE = 3;
    let pageNumbers = $derived.by(() => {
        const start = Math.max(1, currentPage - RANGE);
        const end = Math.min(totalPages, currentPage + RANGE);
        const pages: number[] = [];
        for (let i = start; i <= end; i++) pages.push(i);
        return pages;
    });

    async function loadData(page: number) {
        loading = true;
        error = null;
        try {
            const qs = new URLSearchParams({
                page: page.toString(),
                page_size: pageSize.toString(),
            }).toString();
            const res = await fetch(`/api/nodes/types/${type_name}?${qs}`);
            if (!res.ok) throw new Error("Failed to fetch");
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
                data_type: e.data_type,
            }));
            totalItems = data.total || 0;
        } catch (err: any) {
            error = err.message || "Failed to load";
        } finally {
            loading = false;
        }
    }

    $effect(() => {
        const page = parseInt(searchParams.get("page") || "1", 10);
        currentPage = isNaN(page) || page < 1 ? 1 : page;
        loadData(currentPage);
    });
</script>

<Container class="my-2" fluid>
    <h4>Type: {type_name}</h4>
    {#if loading}
        <div class="text-center py-5"><Spinner /></div>
    {:else if error}
        <p class="text-danger">Error: {error}</p>
    {:else if items.length === 0}
        <p class="text-muted">No resources of type "{type_name}" found.</p>
    {:else}
        <p class="text-muted">
            {totalItems} results (Page {currentPage} / {totalPages})
        </p>
        <ListGroup class="mt-2">
            {#each items as item}
                <ResourceItem {item} />
            {/each}
        </ListGroup>

        {#if totalPages > 1}
            <Pagination>
                <PaginationItem disabled={currentPage <= 1}>
                    <PaginationLink
                        first
                        href={router.p("/types/{type_name}", {
                            search: { page: 1 },
                        })}
                    />
                </PaginationItem>
                <PaginationItem disabled={currentPage <= 1}>
                    <PaginationLink
                        previous
                        href={router.p("/types/{type_name}", {
                            search: { page: currentPage - 1 },
                        })}
                    />
                </PaginationItem>
                {#each pageNumbers as num}
                    <PaginationItem active={num === currentPage}>
                        <PaginationLink
                            href={router.p("/types/{type_name}", {
                                search: { page: num },
                            })}>{num}</PaginationLink
                        >
                    </PaginationItem>
                {/each}
                <PaginationItem disabled={currentPage >= totalPages}>
                    <PaginationLink
                        next
                        href={router.p("/types/{type_name}", {
                            search: { page: currentPage + 1 },
                        })}
                    />
                </PaginationItem>
                <PaginationItem disabled={currentPage >= totalPages}>
                    <PaginationLink
                        last
                        href={router.p("/types/{type_name}", {
                            search: { page: totalPages },
                        })}
                    />
                </PaginationItem>
            </Pagination>
        {/if}
    {/if}
</Container>
