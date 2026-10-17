<script lang="ts">
    import {
        Badge,
        Card,
        CardBody,
        CardFooter,
        CardTitle,
    } from "@sveltestrap/sveltestrap";
    import type { ItemMeta } from "../types";
    import { getContext } from "svelte";
    import { hasRole, getAuthContext } from "../lib/auth.js";
    import {
        statusColor,
        statusLabel,
        typeColor,
        visibilityColor,
    } from "../lib/utils/ui";
    import TagChip from "./ui/TagChip.svelte";

    let {
        item,
        class: className = "",
    }: {
        item: ItemMeta;
        class?: string;
    } = $props();
    let metahub_host = (getContext("mh_host") as string) || "";

    let canEdit = $derived(
        hasRole("nodes:edit_any") ||
        (item.creator_sub === getAuthContext()?.user?.sub)
    );
</script>

<Card class="position-relative shadow-sm {item.data_type ? 'ps-4' : ''} {className}">
    {#if item.data_type}
        <div
            class="type-bar text-white"
            style="background:{typeColor(item.data_type)}"
            title={item.data_type}
        >
            <a class="type-text" href="/types/{encodeURI(item.data_type)}"
                >{item.data_type}</a
            >
        </div>
    {/if}

    <CardBody class="pb-2">
        <div class="d-flex justify-content-between align-items-start gap-2">
            <div class="item-main">
                <CardTitle class="h6 mb-1">
                    <a class="item-title" href="/items/{item.id}">{item.title}</a>
                </CardTitle>
                {#if item.description}
                    <p class="item-description text-secondary small mb-0" title={item.description}>
                        {item.description}
                    </p>
                {/if}
            </div>
            <div class="d-flex align-items-center gap-1 flex-shrink-0">
                {#if item.visibility && item.visibility !== "public"}
                    <Badge class="text-bg-{visibilityColor(item.visibility)}">
                        {item.visibility}
                    </Badge>
                {/if}
                <Badge class="text-bg-{statusColor(item.status)}">
                    {statusLabel(item.status)}
                </Badge>
            </div>
        </div>
    </CardBody>

    <CardFooter class="py-2 d-flex flex-wrap align-items-center gap-2">
        <div class="d-flex flex-wrap gap-1 flex-grow-1">
            {#each item.tags as tag}
                <TagChip {tag} metahubHost={metahub_host} />
            {/each}
        </div>
        <div class="d-flex flex-wrap align-items-center gap-2 small text-secondary ms-auto">
            {#if item.creator_name}
                <span>{item.creator_name}</span>
                <span>·</span>
            {/if}
            <span>{item.update_time.toLocaleDateString()}</span>
            {#if canEdit}
                <a class="link-primary text-decoration-none" href="/items/{item.id}?edit=1">
                    Edit
                </a>
            {/if}
        </div>
    </CardFooter>
</Card>

<style>
    .item-main {
        min-width: 0;
    }
    .item-title {
        color: var(--bs-body-color);
        text-decoration: none;
    }
    .item-title:hover {
        color: var(--bs-link-hover-color);
        text-decoration: underline;
    }
    .item-description {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .type-bar {
        display: flex;
        align-items: center;
        justify-content: center;
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 1.5rem;
        overflow: hidden;
        border-top-left-radius: var(--bs-border-radius);
        border-bottom-left-radius: var(--bs-border-radius);
    }
    .type-text {
        writing-mode: vertical-rl;
        text-orientation: mixed;
        transform: rotate(180deg);
        font-weight: 600;
        font-size: 12px;
        white-space: nowrap;
        color: inherit;
        text-decoration: none;
    }
</style>
