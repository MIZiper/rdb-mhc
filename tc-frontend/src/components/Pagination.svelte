<script lang="ts">
    import {
        Pagination,
        PaginationItem,
        PaginationLink,
    } from "@sveltestrap/sveltestrap";

    let {
        page,
        totalPages,
        onchange,
        range = 3,
    }: {
        page: number;
        totalPages: number;
        onchange: (page: number) => void;
        range?: number;
    } = $props();

    let pageNumbers = $derived.by(() => {
        const start = Math.max(1, page - range);
        const end = Math.min(totalPages, page + range);
        const pages: number[] = [];
        for (let i = start; i <= end; i++) pages.push(i);
        return pages;
    });

    function go(target: number) {
        if (target < 1 || target > totalPages || target === page) return;
        onchange(target);
    }
</script>

{#if totalPages > 1}
    <Pagination>
        <PaginationItem disabled={page <= 1}>
            <PaginationLink first onclick={() => go(1)} />
        </PaginationItem>
        <PaginationItem disabled={page <= 1}>
            <PaginationLink previous onclick={() => go(page - 1)} />
        </PaginationItem>
        {#each pageNumbers as num}
            <PaginationItem active={num === page}>
                <PaginationLink onclick={() => go(num)}>{num}</PaginationLink>
            </PaginationItem>
        {/each}
        <PaginationItem disabled={page >= totalPages}>
            <PaginationLink next onclick={() => go(page + 1)} />
        </PaginationItem>
        <PaginationItem disabled={page >= totalPages}>
            <PaginationLink last onclick={() => go(totalPages)} />
        </PaginationItem>
    </Pagination>
{/if}
