<script lang="ts">
    import {
        Container,
        ListGroup,
        Nav,
        NavItem,
        NavLink,
    } from "@sveltestrap/sveltestrap";
    import { getContext, onMount } from "svelte";
    import { searchParams } from "sv-router";
    import ResourceItem from "../components/ResourceItem.svelte";
    import Pagination from "../components/Pagination.svelte";
    import { authFetch } from "../lib/auth";
    import { useNodeList } from "../lib/useNodeList.svelte";

    const STATUS_TABS = [
        { key: "", label: "All" },
        { key: "draft", label: "Draft" },
        { key: "pending_review", label: "In Review" },
        { key: "published", label: "Published" },
        { key: "archived", label: "Archived" },
    ];

    const metahubHost = (getContext("mh_host") as string) || "";
    const list = useNodeList(metahubHost, 10);
    let activeTab = $state("");

    function load(status: string, page: number) {
        activeTab = status;
        const params = new URLSearchParams({
            page: String(page),
            page_size: "10",
        });
        if (status) params.set("status", status);
        list.load(
            () => authFetch(`/api/nodes/mine?${params.toString()}`).then((r) => r.json()),
            page,
        );
    }

    function urlFor(status: string, page: number): string {
        const params: Record<string, string> = { page: String(page) };
        if (status) params.status = status;
        return `/mine?${new URLSearchParams(params).toString()}`;
    }

    function switchTab(status: string) {
        window.history.pushState({}, "", urlFor(status, 1));
        load(status, 1);
    }

    function goPage(page: number) {
        window.history.pushState({}, "", urlFor(activeTab, page));
        load(activeTab, page);
    }

    onMount(() => {
        const status = String(searchParams.get("status") || "");
        const page = parseInt(String(searchParams.get("page") || "1"), 10);
        load(status, isNaN(page) || page < 1 ? 1 : page);
    });
</script>

<Container class="my-2" fluid>
    <h4>My Workspace</h4>

    <Nav tabs class="mb-3">
        {#each STATUS_TABS as tab}
            <NavItem>
                <NavLink active={activeTab === tab.key} onclick={() => switchTab(tab.key)}>
                    {tab.label}
                </NavLink>
            </NavItem>
        {/each}
    </Nav>

    {#if list.loading}
        <p>Loading...</p>
    {:else if list.error}
        <p class="alert alert-danger">{list.error}</p>
    {:else if list.items.length === 0}
        <p>No items found.</p>
    {:else}
        <p class="meta">
            {list.total} results (Page {list.page} / {list.totalPages})
        </p>

        <ListGroup class="mt-2">
            {#each list.items as item}
                <ResourceItem {item} />
            {/each}
        </ListGroup>

        <Pagination
            page={list.page}
            totalPages={list.totalPages}
            onchange={goPage}
        />
    {/if}
</Container>
