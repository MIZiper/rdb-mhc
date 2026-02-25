<script lang="ts">
    import {
        Button,
        Col,
        Container,
        Input,
        ListGroup,
        Pagination,
        PaginationItem,
        PaginationLink,
        Row,
    } from "@sveltestrap/sveltestrap";
    import ResourceItem from "../lib/ResourceItem.svelte";
    import type { ItemMeta } from "../schema";
    import { onMount } from "svelte";
    import { p as pp, navigate } from "../router";

    let searchBind = $state("");
    let qSearch = $state("");

    let items: ItemMeta[] = $state([]);
    let loading = $state(false);
    let error = $state(null);

    const pageSize = 10;
    const RANGE = 3;
    let currentPage = $state(1);
    let totalItems = $state(0);
    let totalPages = $derived(Math.ceil(totalItems / pageSize));
    let pageNumbers = $derived.by(() => {
        const start = Math.max(1, currentPage - RANGE);
        const end = Math.min(totalPages, currentPage + RANGE);

        const pages = [];
        for (let i = start; i <= end; i++) {
            pages.push(i);
        }
        return pages;
    });

    async function loadData(q: string, page: number) {
        loading = true;
        error = null;

        try {
            const apiParams = {
                page: page.toString(),
                q: q || "",
            };

            const qs = new URLSearchParams(apiParams).toString();
            const res = await fetch(`/api/nodes/?${qs}`);
            if (!res.ok) throw new Error("Failed to fetch");
            const data = await res.json();

            items = data.items.map((e) => ({
                id: e.id,
                title: e.title,
                description: e.description,
                update_time: new Date(e.updated_at),
                tags: [],
            }));

            totalItems = data.total || 0;
        } catch (err: any) {
            error = err.message || "加载失败";
            console.error(err);
        } finally {
            loading = false;
        }
    }

    onMount(async () => {
        const params = new URLSearchParams(location.search);
        const q = params.get("q") || "";
        const page = parseInt(params.get("page") || "1", 10);

        qSearch = q;
        searchBind = q;
        currentPage = isNaN(page) || page < 1 ? 1 : page;

        await loadData(q, page);
    });

    function handleSearch() {
        const q = searchBind.trim();
        let params;
        if (q) {
            params = new URLSearchParams({ q, page: "1" });
        } else {
            params = new URLSearchParams({ page: "1" });
        }

        navigate("/", { search: params.toString() });

        loadData(q, 1).then(() => {
            currentPage = 1;
            qSearch = q;
        });
    }
</script>

<svelte:head>
    <title>RDB (page: {currentPage}, q: {qSearch})</title>
</svelte:head>

<Container class="my-2" fluid>
    <Row>
        <Col>
            <Input
                type="search"
                placeholder="Search by text"
                bind:value={searchBind}
            />
        </Col>
        <Col xs="auto">
            <Button onclick={handleSearch}>Search</Button>
        </Col>
    </Row>

    {#if loading}
        <p>加载中...</p>
    {:else if error}
        <p class="error">出错啦: {error}</p>
    {:else if items.length === 0}
        <p>暂无数据匹配。</p>
    {:else}
        <p class="meta">
            共 {totalItems} 个结果 (第 {currentPage} / {totalPages} 页)
        </p>

        <ListGroup class="mt-2">
            {#each items as item}
                <ResourceItem {item} />
            {/each}
        </ListGroup>

        <Pagination>
            <PaginationItem disabled={currentPage <= 1}>
                <PaginationLink
                    first
                    href={`?page=${1}` + (qSearch ? `&q=${qSearch}` : "")}
                />
            </PaginationItem>
            <PaginationItem disabled={currentPage <= 1}>
                <PaginationLink
                    previous
                    href={`?page=${currentPage - 1}` +
                        (qSearch ? `&q=${qSearch}` : "")}
                />
            </PaginationItem>
            {#each pageNumbers as num}
                <PaginationItem active={num === currentPage}>
                    <PaginationLink
                        href={`?page=${num}` + (qSearch ? `&q=${qSearch}` : "")}
                        >{num}</PaginationLink
                    >
                </PaginationItem>
            {/each}
            <PaginationItem disabled={currentPage >= totalPages}>
                <PaginationLink
                    next
                    href={`?page=${currentPage + 1}` +
                        (qSearch ? `&q=${qSearch}` : "")}
                />
            </PaginationItem>
            <PaginationItem disabled={currentPage >= totalPages}>
                <PaginationLink
                    last
                    href={`?page=${totalPages}` +
                        (qSearch ? `&q=${qSearch}` : "")}
                />
            </PaginationItem>
        </Pagination>
    {/if}
</Container>
