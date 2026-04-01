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

    import type { ItemDetail } from "../schema";
    import { getContext, onMount, type Component } from "svelte";
    import { construct_tags_by_ids, fetch_tags_info } from "./FetchMetaHubTags";
    import { registry, type BaseProcessor } from "../lib/processor";

    let router: any = getContext("router");
    let item_id = router.route.getParams("/items/:id").id;
    let item: ItemDetail | null = $state(null);
    let metahub_host = (getContext("mh_host") as string) || "";
    let processor: BaseProcessor | null = $state(null);

    onMount(async () => {
        const res = await fetch(`/api/nodes/${item_id}/data`);
        const data = await res.json();

        const tags_cache = await fetch_tags_info(metahub_host, data.tag_ids);

        item = {
            id: data.name,
            title: data.title,
            description: data.description,
            update_time: data.update_date,
            tags: construct_tags_by_ids(data.tag_ids, tags_cache),
            data_type: data.data_type,
            content: data.content,
        };

        processor = registry.getProcessor(item.data_type);
    });
</script>

<Container class="my-2" fluid>
    <Row>
        <Col>
            {#if item}
                {#if !processor}
                    <p>Registered type: [{item.data_type}] (no viewer found)</p>
                    <pre>{JSON.stringify(item.content, null, 2)}</pre>
                {:else}
                    <processor.viewer content={item.content} />
                {/if}
            {:else}
                <p>Loading...</p>
            {/if}
        </Col>
        <Col xs="4">
            {#if item}
                <Card>
                    <CardHeader></CardHeader>
                    <CardBody>
                        <CardSubtitle>{item.title}</CardSubtitle>
                        {item.description}
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
