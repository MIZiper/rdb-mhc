<script lang="ts">
    import {
        Container,
        ListGroup,
        Nav,
        NavItem,
        NavLink,
        Pagination,
        PaginationItem,
        PaginationLink,
    } from "@sveltestrap/sveltestrap";
    import ResourceItem from "../lib/ResourceItem.svelte";
    import type { ItemMeta } from "../schema";
    import { onMount, getContext } from "svelte";
    import { fetch_tags_info, construct_tags_by_ids } from "./FetchMetaHubTags";
    import { authFetch } from "../lib/auth";
    import { searchParams } from "sv-router";

    const STATUS_TABS = [
        { key: "", label: "All" },
        { key: "draft", label: "Draft" },
        { key: "pending_review", label: "In Review" },
        { key: "published", label: "Published" },
        { key: "archived", label: "Archived" },
    ];

    let activeTab = $state("");
    let items: ItemMeta[] = $state([]);
    let loading = $state(false);
    let error = $state("");
    let currentPage = $state(1);
    let totalItems = $state(0);
    const pageSize = 10;
    let totalPages = $derived(Math.ceil(totalItems / pageSize));

    let metahub_host = (getContext("mh_host") as string) || "";

    onMount(() => {
        const statusParam = searchParams.get("status") || "";
        const page = parseInt(searchParams.get("page") || "1", 10);
        activeTab = statusParam;
        currentPage = isNaN(page) || page < 1 ? 1 : page;
        loadItems();
    });

    async function loadItems() {
        loading = true;
        error = "";
        try {
            const params = new URLSearchParams({
                page: currentPage.toString(),
                page_size: pageSize.toString(),
            });
            if (activeTab) params.set("status", activeTab);

            const res = await authFetch(`/api/nodes/mine?${params.toString()}`);
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Failed to load");
            const data = await res.json();

            const uniqueTagIds = [
                ...new Set(data.items.flatMap((item: any) => item.tag_ids)),
            ] as number[];

            let tags_cache: Record<number, any> = {};
            if (uniqueTagIds.length > 0 && metahub_host) {
                tags_cache = await fetch_tags_info(metahub_host, uniqueTagIds);
            }

            items = data.items.map((e: any) => ({
                id: e.id,
                title: e.title,
                description: e.description,
                update_time: new Date(e.updated_at),
                tags: construct_tags_by_ids(e.tag_ids, tags_cache),
                data_type: e.data_type,
                creator_name: e.creator_name,
                creator_sub: e.creator_sub,
                status: e.status,
                visibility: e.visibility || "public",
            }));

            totalItems = data.total || 0;
        } catch (err: any) {
            error = err.message || "Failed to load";
        } finally {
            loading = false;
        }
    }

    function switchTab(tab: string) {
        activeTab = tab;
        currentPage = 1;
        const params: Record<string, string> = {};
        if (tab) params.status = tab;
        params.page = "1";
        const qs = new URLSearchParams(params).toString();
        window.history.pushState({}, "", `/mine?${qs}`);
        loadItems();
    }

    const pageNumbers = $derived.by(() => {
        const RANGE = 3;
        const start = Math.max(1, currentPage - RANGE);
        const end = Math.min(totalPages, currentPage + RANGE);
        const pages = [];
        for (let i = start; i <= end; i++) pages.push(i);
        return pages;
    });
</script>

<Container class="my-2" fluid>
    <h4>My Workspace</h4>

    <Nav tabs class="mb-3">
        {#each STATUS_TABS as tab}
            <NavItem>
                <NavLink
                    active={activeTab === tab.key}
                    onclick={() => switchTab(tab.key)}
                >
                    {tab.label}
                </NavLink>
            </NavItem>
        {/each}
    </Nav>

    {#if loading}
        <p>Loading...</p>
    {:else if error}
        <p class="alert alert-danger">{error}</p>
    {:else if items.length === 0}
        <p>No items found.</p>
    {:else}
        <p class="meta">
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
                        href={`/mine?status=${activeTab}&page=1`}
                    />
                </PaginationItem>
                <PaginationItem disabled={currentPage <= 1}>
                    <PaginationLink
                        previous
                        href={`/mine?status=${activeTab}&page=${currentPage - 1}`}
                    />
                </PaginationItem>
                {#each pageNumbers as num}
                    <PaginationItem active={num === currentPage}>
                        <PaginationLink
                            href={`/mine?status=${activeTab}&page=${num}`}>{num}</PaginationLink>
                    </PaginationItem>
                {/each}
                <PaginationItem disabled={currentPage >= totalPages}>
                    <PaginationLink
                        next
                        href={`/mine?status=${activeTab}&page=${currentPage + 1}`}
                    />
                </PaginationItem>
                <PaginationItem disabled={currentPage >= totalPages}>
                    <PaginationLink
                        last
                        href={`/mine?status=${activeTab}&page=${totalPages}`}
                    />
                </PaginationItem>
            </Pagination>
        {/if}
    {/if}
</Container>
