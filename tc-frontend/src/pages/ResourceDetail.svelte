<script lang="ts">
    import {
        Badge,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardSubtitle,
        CardTitle,
        Col,
        Container,
        Row,
    } from "@sveltestrap/sveltestrap";
    import { route } from "../router";
    import type { ItemDetail } from "../schema";
    import { getContext, onMount } from "svelte";
    import { construct_tags_by_ids, fetch_tags_info } from "./FetchMetaHubTags";

    let item_id = route.getParams("/items/:id").id;
    let item: ItemDetail | null = $state(null);
    let metahub_host = (getContext("mh_host") as string) || "";

    onMount(async () => {
        const res = await fetch(`/api/nodes/${item_id}`);
        const data = await res.json();

        const tags_cache = await fetch_tags_info(metahub_host, data.tag_ids);

        item = {
            id: data.name,
            title: data.title,
            description: data.description,
            update_time: data.update_date,
            tags: construct_tags_by_ids(data.tag_ids, tags_cache),
        };
    });
</script>

<Container fluid>
    <Row>
        <Col>
            <p>Content of the item</p>
        </Col>
        <Col>
            {#if item}
                <Card>
                    <CardHeader>
                        <CardTitle>{item.title}</CardTitle>
                    </CardHeader>
                    <CardBody>
                        <CardSubtitle>{item.description}</CardSubtitle>
                    </CardBody>
                    <CardFooter>
                        {#each item.tags as tag}
                            <Badge
                                pill
                                class="me-1"
                                href="/tags/{tag.id}/{encodeURI(tag.name)}"
                            >
                                {tag.name}
                            </Badge>
                        {/each}
                    </CardFooter>
                </Card>
            {:else}
                <p>Loading</p>
            {/if}
        </Col>
    </Row>
</Container>
