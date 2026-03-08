<script lang="ts">
    import {
        Button,
        ButtonGroup,
        Col,
        Container,
        Input,
        ListGroup,
        Row,
    } from "@sveltestrap/sveltestrap";
    import ResourceItem from "../lib/ResourceItem.svelte";
    import type { ItemMeta, Tag } from "../schema";
    import { getContext, onMount } from "svelte";
    import { fetch_tags_info, construct_tags_by_ids } from "./FetchMetaHubTags";

    let router: any = getContext("router");

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

    let metahub_host = (getContext("mh_host") as string) || "";
    async function loadData(q: string, page: number) {
        loading = true;
        error = null;

        try {
            const apiParams = {
                page: page.toString(),
                q: q || "",
                page_size: pageSize.toString(),
            };

            const qs = new URLSearchParams(apiParams).toString();
            const res = await fetch(`/api/nodes/?${qs}`);
            if (!res.ok) throw new Error("Failed to fetch");
            const data = await res.json();

            const uniqueTagIds = [
                ...new Set(data.items.flatMap((item: any) => item.tag_ids)),
            ] as number[];

            const tags_cache = await fetch_tags_info(
                metahub_host,
                uniqueTagIds,
            );

            items = data.items.map((e: any) => ({
                id: e.id,
                title: e.title,
                description: e.description,
                update_time: new Date(e.updated_at),
                tags: construct_tags_by_ids(e.tag_ids, tags_cache),
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

    function updateItems(q: string = "", page: number = 1) {
        const searchParams = new URLSearchParams();

        if (q) searchParams.set("q", q);
        if (page) searchParams.set("page", page.toString());

        const params = Object.fromEntries(searchParams);
        router.navigate("/", { search: params, replace: true });
        loadData(q, page).then(() => {
            currentPage = page;
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
                onkeypress={(e)=>{if (e.key=="Enter") updateItems(searchBind.trim())}}
            />
        </Col>
        <Col xs="auto">
            <Button onclick={() => updateItems(searchBind.trim())}
                >Search</Button
            >
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

        <ButtonGroup>
            <Button
                disabled={currentPage <= 1}
                onclick={() => updateItems(qSearch, 1)}>«</Button
            >

            <Button
                disabled={currentPage <= 1}
                onclick={() => updateItems(qSearch, currentPage - 1)}>‹</Button
            >
            {#each pageNumbers as num}
                <Button
                    active={num === currentPage}
                    onclick={() => updateItems(qSearch, num)}>{num}</Button
                >
            {/each}

            <Button
                disabled={currentPage >= totalPages}
                onclick={() => updateItems(qSearch, currentPage + 1)}>›</Button
            >

            <Button
                disabled={currentPage >= totalPages}
                onclick={() => updateItems(qSearch, totalPages)}>»</Button
            >
        </ButtonGroup>
    {/if}
</Container>
