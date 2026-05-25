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
    import ResourceItem from "../lib/ResourceItem.svelte";
    import type { ItemMeta } from "../schema";
    import { getContext } from "svelte";
    import { fetch_tags_info, construct_tags_by_ids } from "./FetchMetaHubTags";
    import { searchParams } from "sv-router";
    import { registry } from "../lib/processor";

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
            const res = await fetch(`/api/nodes/types/${encodeURIComponent(type_name)}?${qs}`);
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
                creator_name: e.creator_name,
                creator_sub: e.creator_sub,
                status: e.status,
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
            const results: { title: string; content: any }[] = [];
            for (const id of ids) {
                const res = await fetch(`/api/nodes/${id}/data`);
                if (!res.ok) continue;
                const d = await res.json();
                results.push({ title: d.title, content: d.content });
            }
            analyzedItems = results;
        } finally {
            analyzing = false;
        }
    }

    $effect(() => {
        const page = parseInt(String(searchParams.get("page") || "1"), 10);
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
                <div class="topbar-right">
                    {#if hasManualSelection}
                        <span class="selection-info">{selectedIds.size} selected</span>
                    {/if}
                    <button class="panel-toggle" onclick={() => { panelOpen = !panelOpen }}>
                        {panelOpen ? "◀" : "▶"} Items
                    </button>
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
                        <button class="panel-close" onclick={() => { panelOpen = false }}>×</button>
                    </div>

                    {#if loading}
                        <div class="text-center py-3"><Spinner size="sm" /></div>
                    {:else if error}
                        <p class="text-danger px-2">Error: {error}</p>
                    {:else if items.length === 0}
                        <p class="text-muted px-2">No items of type "{type_name}".</p>
                    {:else}
                        <div class="panel-toolbar">
                            <label class="select-all-label"><input type="checkbox" checked={allPageChecked} onchange={toggleAll} /> Select page</label>
                            {#if selectedIds.size > 0}
                                <button class="btn-clear" onclick={clearAll}>Clear all</button>
                            {/if}
                        </div>
                        <div class="panel-list">
                            {#each items as item (item.id)}
                                <label class="panel-item" class:checked={selectedIds.has(item.id!)}>
                                    <input
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
            <ListGroup class="mt-2">
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
        gap: 12px;
        padding: 8px 0;
        border-bottom: 1px solid #e0e0e0;
        flex-shrink: 0;
    }
    .type-title {
        margin: 0;
        flex: 1;
    }
    .topbar-right {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .selection-info {
        font-size: 0.8em;
        color: #49a9a7;
        background: #e8f5f4;
        padding: 2px 8px;
        border-radius: 3px;
    }
    .panel-toggle {
        border: 1px solid #ccc;
        border-radius: 4px;
        background: #fff;
        padding: 4px 10px;
        cursor: pointer;
        font-size: 0.85em;
        white-space: nowrap;
    }
    .panel-toggle:hover {
        background: #f0f0f0;
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
        padding: 8px 0;
    }
    .hint {
        margin-top: 40px;
        text-align: center;
    }

    .panel-overlay {
        display: block;
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.2);
        z-index: 5;
    }

    .slide-panel {
        position: absolute;
        right: 0;
        top: 0;
        bottom: 0;
        width: 320px;
        background: #fff;
        border-left: 1px solid #ddd;
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
        padding: 8px 12px;
        border-bottom: 1px solid #e0e0e0;
        font-weight: 600;
        font-size: 0.9em;
        flex-shrink: 0;
    }
    .panel-close {
        border: none;
        background: none;
        font-size: 1.3em;
        cursor: pointer;
        color: #999;
        padding: 0 4px;
    }
    .panel-close:hover { color: #333; }
    .panel-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 12px;
        font-size: 0.8em;
        border-bottom: 1px solid #f0f0f0;
        flex-shrink: 0;
    }
    .select-all-label {
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .btn-clear {
        border: 1px solid #ddd;
        border-radius: 3px;
        background: #fff;
        color: #c00;
        cursor: pointer;
        font-size: 0.85em;
        padding: 2px 8px;
    }
    .btn-clear:hover {
        background: #fff0f0;
    }
    .panel-list {
        flex: 1;
        overflow-y: auto;
    }
    .panel-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 8px 12px;
        border-bottom: 1px solid #f5f5f5;
        cursor: pointer;
        transition: background 0.1s;
        font-size: 0.85em;
    }
    .panel-item:hover { background: #f9f9f9; }
    .panel-item.checked { background: #e8f5f4; }
    .panel-item input[type="checkbox"] {
        margin-top: 2px;
        flex-shrink: 0;
    }
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
        color: #888;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .panel-actions {
        padding: 6px 12px;
        border-top: 1px solid #e0e0e0;
        flex-shrink: 0;
    }
    .panel-pagination {
        padding: 8px 4px;
        border-top: 1px solid #e0e0e0;
        flex-shrink: 0;
        overflow-x: auto;
    }
</style>
