<script lang="ts">
    import {
        Badge,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardSubtitle,
        CardText,
        CardTitle,
        Icon,
        NavLink,
    } from "@sveltestrap/sveltestrap";
    import type { ItemMeta } from "../schema";
    import { getContext } from "svelte";

    let { item }: { item: ItemMeta } = $props();
    let metahub_host = (getContext("mh_host") as string) || "";
</script>

<Card class="mb-1">
    <CardBody>
        <CardSubtitle style="border-left: 4px solid gray; padding-left: 6px;">
            <NavLink href="/items/{item.id}">{item.title}</NavLink>
        </CardSubtitle>
        <p class="update_date">
            Update: {item.update_time.toLocaleDateString()}
        </p>
        <CardText>{item.description}</CardText>
    </CardBody>
    <CardFooter>
        {#each item.tags as tag}
            <Badge pill class="me-1" href="/tags/{tag.id}/{encodeURI(tag.name)}">
                {tag.name}
                <a href={`${metahub_host}/registered/${tag.id}/${encodeURI(tag.name)}`}>🔗</a>
            </Badge>
        {/each}
    </CardFooter>
</Card>

<style>
    p.update_date {
        position: absolute;
        top: 5px;
        right: 5px;
        color: gray;
        font-size: smaller;
    }
</style>
