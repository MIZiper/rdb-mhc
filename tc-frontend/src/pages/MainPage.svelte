<script lang="ts">
    import {
        Button,
        ButtonGroup,
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
    import type { ItemMeta, Tag } from "../schema";
    import { getContext, onMount } from "svelte";
    import { fetch_tags_info, construct_tags_by_ids } from "./FetchMetaHubTags";
    import { searchParams } from "sv-router";

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

    $effect(() => {
        const q = searchParams.get("q") || "";
        const page = parseInt(searchParams.get("page") || "1", 10);

        loadData(String(q), Number(page)).then(() => {
            qSearch = q;
            searchBind = q;
            currentPage = isNaN(page) || page < 1 ? 1 : page;
        });
    });
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
                onkeypress={(e) => {
                    if (e.key == "Enter")
                        router.navigate("/", {
                            search: { q: searchBind.trim() },
                        });
                }}
            />
        </Col>
        <Col xs="auto">
            <Button
                onclick={() =>
                    router.navigate("/", { search: { q: searchBind.trim() } })}
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

        <Pagination>
            <PaginationItem disabled={currentPage <= 1}>
                <PaginationLink
                    first
                    href={router.p("/", { search: { q: qSearch, page: 1 } })}
                />
            </PaginationItem>
            <PaginationItem disabled={currentPage <= 1}>
                <PaginationLink
                    previous
                    href={router.p("/", {
                        search: { q: qSearch, page: currentPage - 1 },
                    })}
                />
            </PaginationItem>
            {#each pageNumbers as num}
                <PaginationItem active={num === currentPage}>
                    <PaginationLink
                        href={router.p("/", {
                            search: { q: qSearch, page: num },
                        })}>{num}</PaginationLink
                    >
                </PaginationItem>
            {/each}
            <PaginationItem disabled={currentPage >= totalPages}>
                <PaginationLink
                    next
                    href={router.p("/", {
                        search: { q: qSearch, page: currentPage + 1 },
                    })}
                />
            </PaginationItem>
            <PaginationItem disabled={currentPage >= totalPages}>
                <PaginationLink
                    last
                    href={router.p("/", {
                        search: { q: qSearch, page: totalPages },
                    })}
                />
            </PaginationItem>
        </Pagination>
    {/if}
</Container>
