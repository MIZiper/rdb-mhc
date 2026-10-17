<script lang="ts">
    let {
        tag,
        metahubHost = "",
        link = true,
        class: className = "",
    }: {
        tag: { id: number | null; name: string };
        metahubHost?: string;
        link?: boolean;
        class?: string;
    } = $props();

    const tagHref = $derived(
        tag.id == null ? "#" : `/tags/${tag.id}/${encodeURIComponent(tag.name)}`,
    );
    const metahubHref = $derived(
        metahubHost && tag.id != null
            ? `${metahubHost}/registered/${tag.id}/${encodeURIComponent(tag.name)}`
            : "",
    );
</script>

<span class="badge rounded-pill tag-chip {className}">
    {#if link}
        <a class="tag-name" href={tagHref}>{tag.name}</a>
    {:else}
        <span class="tag-name">{tag.name}</span>
    {/if}
    {#if link && metahubHref}
        <a
            class="tag-ext"
            href={metahubHref}
            target="_blank"
            rel="noreferrer"
            title="Open in MetaHub"
        >↗</a>
    {/if}
</span>

<style>
    .tag-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border: 1px solid var(--bs-border-color);
        background: var(--bs-tertiary-bg);
        color: var(--bs-body-color);
        font-weight: 500;
        text-decoration: none;
    }
    .tag-name {
        color: inherit;
        text-decoration: none;
    }
    .tag-name:hover {
        color: var(--bs-link-hover-color);
    }
    .tag-ext {
        color: var(--bs-secondary-color);
        font-size: 0.75em;
        line-height: 1;
        text-decoration: none;
    }
    .tag-ext:hover {
        color: var(--bs-link-hover-color);
    }
</style>
