<script lang="ts">
    import {
        Container,
        ListGroup,
        Pagination,
        PaginationItem,
        PaginationLink,
    } from "@sveltestrap/sveltestrap";
    import Searchbar from "../lib/Searchbar.svelte";
    import ResourceItem from "../lib/ResourceItem.svelte";
    import type { ItemMeta } from "../schema";

    let items: ItemMeta[] = $state([]);
    for (let index = 0; index < 7; index++) {
        items.push({
            title: `Item ${index}`,
            description: "Blah blah blah blah",
            tags: [],
            id: index,
            update_time: new Date(),
        });
    }
</script>

<Container class="my-2" fluid>
    <Searchbar />
    <ListGroup>
        {#each items as item}
            <ResourceItem {item} />
        {/each}
    </ListGroup>

    <Pagination>
        <PaginationItem>
            <PaginationLink first href="#" />
        </PaginationItem>
        <PaginationItem>
            <PaginationLink last href="#" />
        </PaginationItem>
    </Pagination>
</Container>
