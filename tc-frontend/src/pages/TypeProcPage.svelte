<script lang="ts">
    import {
        Container,
        ListGroup,
        Pagination,
        PaginationItem,
        PaginationLink,
        Spinner,
        Button,
    } from "@sveltestrap/sveltestrap";
    import ResourceItem from "../components/ResourceItem.svelte";
    import type { ItemMeta } from "../types";
    import { getContext } from "svelte";
    import { fetchTagsInfo, constructTagsById } from "../lib/api/metahub";
    import { searchParams } from "sv-router";
    import { registry } from "../modules/registry";
    import { authFetch, getAuthContext } from "../lib/auth";

    let router: any = getContext("router");
    const type_name = router.route.getParams("/types/:type_name").type_name;
    let metahub_host = (getContext("mh_host") as string) || "";

    let processor = $derived(registry.getProcessor(type_name));

    let items: ItemMeta[] = $state([]);
    let loading: boolean = $state(true);
    let error: string | null = $state(null);

    const pageSize = 10;
    let currentPage = $state(1);
    let totalItems = $state(0);
    let totalPages = $derived(Math.ceil(totalItems / pageSize));

    const RANGE = 3;
    let pageNumbers = $derived.by(() => {
        const start = Math.max(1, currentPage - RANGE);
        const end = Math.min(totalPages, currentPage + RANGE);
        const pages: number[] = [];
        for (let i = start; i <= end; i++) pages.push(i);
        return pages;
    });

    let selectedIds: Set<string> = $state(new Set());
    let hasManualSelection: boolean = $state(false);
    let panelOpen: boolean = $state(false);
    let analyzedItems: { title: string; content: any }[] = $state([]);
    let analyzing: boolean = $state(false);
    let initialized: boolean = $state(false);

    async function loadData(page: number) {
        loading = true;
        error = null;
        try {
            const qs = new URLSearchParams({
                page: page.toString(),
                page_size: pageSize.toString(),
            }).toString();
            const res = await authFetch(`/api/nodes/types/${encodeURIComponent(type_name)}?${qs}`);
            if (!res.ok) throw new Error("Failed to fetch");
            const data = await res.json();

            const uniqueTagIds = [
                ...new Set(data.items.flatMap((item: any) => item.tag_ids)),
            ] as number[];

            const tags_cache = await fetchTagsInfo(metahub_host, uniqueTagIds);

            items = data.items.map((e: any) => ({
                id: e.id,
                title: e.title,
                description: e.description,
                update_time: new Date(e.updated_at),
                tags: constructTagsById(e.tag_ids, tags_cache),
                data_type: e.data_type,
                creator_name: e.creator_name,
                creator_sub: e.creator_sub,
                status: e.status,
                visibility: e.visibility || "public",
            }));
            totalItems = data.total || 0;

            if (!initialized) {
                initialized = true;
                const pageIds = items.map(it => it.id!).filter(Boolean);
                await loadContentForIds(pageIds);
            }
        } catch (err: any) {
            error = err.message || "Failed to load";
        } finally {
            loading = false;
        }
    }

    async function loadContentForIds(ids: string[]) {
        analyzing = true;
        try {
            if (ids.length === 0) {
                analyzedItems = [];
                return;
            }
            const res = await authFetch(
                `/api/nodes/data?ids=${encodeURIComponent(ids.join(","))}`,
            );
            if (!res.ok) {
                analyzedItems = [];
                return;
            }
            const d = await res.json();
            analyzedItems = d.items.map((it: any) => ({
                title: it.title,
                content: it.content,
            }));
        } finally {
            analyzing = false;
        }
    }

    $effect(() => {
        const page = parseInt(String(searchParams.get("page") || "1"), 10);
        const _auth = getAuthContext();
        currentPage = isNaN(page) || page < 1 ? 1 : page;
        loadData(currentPage);
    });

    function toggleItem(id: string) {
        const next = new Set(selectedIds);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        selectedIds = next;
        hasManualSelection = true;
    }

    function toggleAll() {
        const pageIds = items.map(it => it.id!).filter(Boolean);
        const allChecked = pageIds.every(id => selectedIds.has(id));
        const next = new Set(selectedIds);
        if (allChecked) {
            for (const id of pageIds) next.delete(id);
        } else {
            for (const id of pageIds) next.add(id);
        }
        selectedIds = next;
        hasManualSelection = true;
    }

    function clearAll() {
        selectedIds = new Set();
        hasManualSelection = false;
    }

    function applySelection() {
        const ids = hasManualSelection && selectedIds.size > 0
            ? [...selectedIds]
            : items.map(it => it.id!).filter(Boolean);
        loadContentForIds(ids);
        panelOpen = false;
    }

    let allPageChecked = $derived.by(() => {
        const pageIds = items.map(it => it.id!).filter(Boolean);
        return pageIds.length > 0 && pageIds.every(id => selectedIds.has(id));
    });
</script>

<Container class="my-2" fluid>
    {#if processor?.typeViewer}
        <div class="viewer-layout">
            <div class="viewer-topbar">
                <h4 class="type-title">Type: {type_name}</h4>
                <div class="d-flex align-items-center gap-2">
                    {#if hasManualSelection}
                        <span class="badge text-bg-primary">{selectedIds.size} selected</span>
                    {/if}
                    <Button size="sm" color="outline-secondary" onclick={() => { panelOpen = !panelOpen }}>
                        {panelOpen ? "◀" : "▶"} Items
                    </Button>
                </div>
            </div>

            <div class="viewer-body">
                <div class="viewer-main">
                    {#if analyzing}
                        <div class="text-center py-5"><Spinner /></div>
                    {:else if analyzedItems.length > 0}
                        <processor.typeViewer items={analyzedItems} />
                    {:else}
                        <p class="text-muted hint">No data available.</p>
                    {/if}
                </div>

                {#if panelOpen}
                    <div class="panel-overlay" role="button" tabindex="-1" onkeydown={(e: KeyboardEvent) => { if (e.key === "Escape") panelOpen = false }} onclick={() => { panelOpen = false }}></div>
                {/if}

                <div class="slide-panel" class:visible={panelOpen}>
                    <div class="panel-header">
                        <span>Items ({totalItems})</span>
                        <Button size="sm" color="link" class="text-secondary px-1" onclick={() => { panelOpen = false }}>×</Button>
                    </div>

                    {#if loading}
                        <div class="text-center py-3"><Spinner size="sm" /></div>
                    {:else if error}
                        <p class="text-danger px-2">Error: {error}</p>
                    {:else if items.length === 0}
                        <p class="text-muted px-2">No items of type "{type_name}".</p>
                    {:else}
                        <div class="panel-toolbar">
                            <label class="form-check m-0">
                                <input class="form-check-input" type="checkbox" checked={allPageChecked} onchange={toggleAll} />
                                <span class="form-check-label">Select page</span>
                            </label>
                            {#if selectedIds.size > 0}
                                <Button size="sm" color="link" class="text-danger p-0" onclick={clearAll}>Clear all</Button>
                            {/if}
                        </div>
                        <div class="panel-list">
                            {#each items as item (item.id)}
                                <label class="panel-item" class:checked={selectedIds.has(item.id!)}>
                                    <input
                                        class="form-check-input mt-1"
                                        type="checkbox"
                                        checked={selectedIds.has(item.id!)}
                                        onchange={() => toggleItem(item.id!)}
                                    />
                                    <div class="panel-item-info">
                                        <div class="panel-item-title">{item.title}</div>
                                        {#if item.description}
                                            <div class="panel-item-desc">{item.description}</div>
                                        {/if}
                                    </div>
                                </label>
                            {/each}
                        </div>

                        <div class="panel-actions">
                            <Button color="primary" size="sm" onclick={applySelection}>Apply</Button>
                        </div>

                        {#if totalPages > 1}
                            <div class="panel-pagination">
                                <Pagination size="sm">
                                    <PaginationItem disabled={currentPage <= 1}>
                                        <PaginationLink first href={router.p("/types/:type_name", { params: { type_name }, search: { page: 1 } })} />
                                    </PaginationItem>
                                    <PaginationItem disabled={currentPage <= 1}>
                                        <PaginationLink previous href={router.p("/types/:type_name", { params: { type_name }, search: { page: currentPage - 1 } })} />
                                    </PaginationItem>
                                    {#each pageNumbers as num}
                                        <PaginationItem active={num === currentPage}>
                                            <PaginationLink href={router.p("/types/:type_name", { params: { type_name }, search: { page: num } })}>{num}</PaginationLink>
                                        </PaginationItem>
                                    {/each}
                                    <PaginationItem disabled={currentPage >= totalPages}>
                                        <PaginationLink next href={router.p("/types/:type_name", { params: { type_name }, search: { page: currentPage + 1 } })} />
                                    </PaginationItem>
                                    <PaginationItem disabled={currentPage >= totalPages}>
                                        <PaginationLink last href={router.p("/types/:type_name", { params: { type_name }, search: { page: totalPages } })} />
                                    </PaginationItem>
                                </Pagination>
                            </div>
                        {/if}
                    {/if}
                </div>
            </div>
        </div>
    {:else}
        <h4>Type: {type_name}</h4>
        {#if loading}
            <div class="text-center py-5"><Spinner /></div>
        {:else if error}
            <p class="text-danger">Error: {error}</p>
        {:else if items.length === 0}
            <p class="text-muted">No resources of type "{type_name}" found.</p>
        {:else}
            <p class="text-muted">{totalItems} results (Page {currentPage} / {totalPages})</p>
            <ListGroup class="mt-2 d-flex flex-column gap-2">
                {#each items as item}
                    <ResourceItem {item} />
                {/each}
            </ListGroup>
            {#if totalPages > 1}
                <Pagination>
                    <PaginationItem disabled={currentPage <= 1}>
                        <PaginationLink first href={router.p("/types/:type_name", { params: { type_name }, search: { page: 1 } })} />
                    </PaginationItem>
                    <PaginationItem disabled={currentPage <= 1}>
                        <PaginationLink previous href={router.p("/types/:type_name", { params: { type_name }, search: { page: currentPage - 1 } })} />
                    </PaginationItem>
                    {#each pageNumbers as num}
                        <PaginationItem active={num === currentPage}>
                            <PaginationLink href={router.p("/types/:type_name", { params: { type_name }, search: { page: num } })}>{num}</PaginationLink>
                        </PaginationItem>
                    {/each}
                    <PaginationItem disabled={currentPage >= totalPages}>
                        <PaginationLink next href={router.p("/types/:type_name", { params: { type_name }, search: { page: currentPage + 1 } })} />
                    </PaginationItem>
                    <PaginationItem disabled={currentPage >= totalPages}>
                        <PaginationLink last href={router.p("/types/:type_name", { params: { type_name }, search: { page: totalPages } })} />
                    </PaginationItem>
                </Pagination>
            {/if}
        {/if}
    {/if}
</Container>

<style>
    .viewer-layout {
        display: flex;
        flex-direction: column;
        height: calc(100vh - 80px);
    }
    .viewer-topbar {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--bs-border-color);
        flex-shrink: 0;
    }
    .type-title {
        margin: 0;
        flex: 1;
    }
    .viewer-body {
        display: flex;
        flex: 1;
        overflow: hidden;
        position: relative;
    }
    .viewer-main {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem 0;
    }
    .hint {
        margin-top: 2.5rem;
        text-align: center;
    }

    .panel-overlay {
        display: block;
        position: absolute;
        inset: 0;
        background: rgba(var(--bs-black-rgb), 0.2);
        z-index: 5;
    }

    .slide-panel {
        position: absolute;
        right: 0;
        top: 0;
        bottom: 0;
        width: 320px;
        background: var(--bs-body-bg);
        border-left: 1px solid var(--bs-border-color);
        transform: translateX(100%);
        transition: transform 0.25s ease;
        z-index: 10;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .slide-panel.visible {
        transform: translateX(0);
    }
    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid var(--bs-border-color);
        font-weight: 600;
        font-size: 0.9em;
        flex-shrink: 0;
    }
    .panel-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.25rem 0.75rem;
        font-size: 0.8em;
        border-bottom: 1px solid var(--bs-border-color-translucent);
        flex-shrink: 0;
    }
    .panel-list {
        flex: 1;
        overflow-y: auto;
    }
    .panel-item {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid var(--bs-border-color-translucent);
        cursor: pointer;
        transition: background 0.1s;
        font-size: 0.85em;
    }
    .panel-item:hover { background: var(--bs-tertiary-bg); }
    .panel-item.checked { background: rgba(var(--bs-primary-rgb), 0.1); }
    .panel-item-info {
        min-width: 0;
    }
    .panel-item-title {
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .panel-item-desc {
        font-size: 0.85em;
        color: var(--bs-secondary-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .panel-actions {
        padding: 0.375rem 0.75rem;
        border-top: 1px solid var(--bs-border-color);
        flex-shrink: 0;
    }
    .panel-pagination {
        padding: 0.5rem 0.25rem;
        border-top: 1px solid var(--bs-border-color);
        flex-shrink: 0;
        overflow-x: auto;
    }
</style>
