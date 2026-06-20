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
    import { hasRole, getAuthContext } from "./auth.js";

    let { item }: { item: ItemMeta } = $props();
    let metahub_host = (getContext("mh_host") as string) || "";

    let canEdit = $derived(
        hasRole("nodes:edit_any") ||
        (item.creator_sub === getAuthContext()?.user?.sub)
    );

    function hashString(s: string) {
        let h = 0;
        for (let i = 0; i < s.length; i++) {
            h = (h << 5) - h + s.charCodeAt(i);
            h |= 0;
        }
        return Math.abs(h);
    }

    function colorFromHash(s: string) {
        const h = hashString(s.split(".")[0]);
        const hue = h % 360;
        return `hsl(${hue} 65% 45%)`;
    }

    function statusColor(status: string): string {
        switch (status) {
            case "draft": return "secondary";
            case "pending_review": return "warning";
            case "published": return "success";
            case "archived": return "dark";
            default: return "secondary";
        }
    }

    function statusLabel(status: string): string {
        switch (status) {
            case "draft": return "Draft";
            case "pending_review": return "In Review";
            case "published": return "Published";
            case "archived": return "Archived";
            default: return status;
        }
    }

    function visibilityColor(visibility: string): string {
        switch (visibility) {
            case "internal": return "info";
            case "confidential": return "danger";
            default: return "light";
        }
    }

    const barTextColor = "white";
</script>

<Card class="mb-1 {item.data_type ? 'ps-2' : ''}">
    <CardBody>
        <CardSubtitle style="border-left: 4px solid gray; padding-left: 6px;">
            <NavLink href="/items/{item.id}">{item.title}</NavLink>
        </CardSubtitle>
        <p class="update_date">
            {#if item.creator_name}
                <span class="creator">{item.creator_name}</span>
            {/if}
            {#if item.visibility && item.visibility !== "public"}
                <Badge color={visibilityColor(item.visibility)} class="ms-1">{item.visibility}</Badge>
            {/if}
            {#if item.status}
                <Badge color={statusColor(item.status)} class="ms-1">{statusLabel(item.status)}</Badge>
            {/if}
            {#if canEdit}
                <NavLink href="/items/{item.id}?edit=1" class="ms-1">Edit</NavLink>
            {/if}
            {item.update_time.toLocaleDateString()}
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
        display: flex;
        align-items: center;
        gap: 6px;
    }
</style>
