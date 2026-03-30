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

    let router: any = getContext("router");
    let item_id = router.route.getParams("/items/:id").id;
    let item: ItemDetail | null = $state(null);
    let metahub_host = (getContext("mh_host") as string) || "";
    let Viewer: Component | null = $state(null);

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
        // Attempt to load a registered viewer for the data_type (if any)
        if (item.data_type) {
            try {
                const mod = await import(`../modules/types/${item.data_type}.svelte`);
                Viewer = mod.default;
            } catch (e) {
                Viewer = null;
            }
        } else {
            Viewer = null;
        }
    });
</script>

<Container fluid>
    <Row>
        <Col>
            {#if item}
                {#if !item.data_type}
                    <pre>{JSON.stringify(item.content, null, 2)}</pre>
                {:else}
                    {#if Viewer}
                        <Viewer content={item.content} />
                    {:else}
                        <p>Registered type: {item.data_type} (no viewer found)</p>
                        <pre>{JSON.stringify(item.content, null, 2)}</pre>
                    {/if}
                {/if}
            {:else}
                <p>Loading...</p>
            {/if}
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
