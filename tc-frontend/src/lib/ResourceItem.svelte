<script lang="ts">
    import {
        Badge,
        Card,
        CardBody,
        CardFooter,
        CardSubtitle,
        CardText,
        NavLink,
    } from "@sveltestrap/sveltestrap";
    import type { ItemMeta } from "../schema";
    import { getContext } from "svelte";

    let { item }: { item: ItemMeta } = $props();
    let metahub_host = (getContext("mh_host") as string) || "";

    function hashString(s: string) {
        let h = 0;
        for (let i = 0; i < s.length; i++) {
            h = (h << 5) - h + s.charCodeAt(i);
            h |= 0;
        }
        return Math.abs(h);
    }

    function colorFromHash(s: string) {
        const h = hashString(s);
        const hue = h % 360;
        return `hsl(${hue} 65% 45%)`;
    }

    const barTextColor = "white";
</script>

<Card class="mb-1 {item.data_type ? 'ps-2' : ''}">
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
            <Badge
                pill
                class="me-1"
                href="/tags/{tag.id}/{encodeURI(tag.name)}"
            >
                {tag.name}
                <a
                    class="metahub-reg"
                    href={`${metahub_host}/registered/${tag.id}/${encodeURI(tag.name)}`}
                    >🔗</a
                >
            </Badge>
        {/each}
    </CardFooter>
    {#if item.data_type}
        <div
            class="type-bar"
            style="background:{colorFromHash(
                item.data_type,
            )}; color:{barTextColor};"
        >
            <a class="type-text" href="/types/{encodeURI(item.data_type)}"
                >{item.data_type}</a
            >
        </div>
    {/if}
</Card>

<style>
    a.metahub-reg {
        text-decoration: none;
    }

    .type-bar {
        display: flex;
        align-items: center;
        justify-content: center;

        position: absolute;
        left: -1px;
        top: -1px;
        bottom: -1px;
    }

    .type-text {
        writing-mode: vertical-rl;
        text-orientation: mixed;
        transform: rotate(180deg);
        font-weight: 600;
        font-size: 12px;
        white-space: nowrap;
        color: white;
        text-decoration: none;
    }

    p.update_date {
        position: absolute;
        top: 5px;
        right: 5px;
        color: gray;
        font-size: smaller;
    }
</style>
