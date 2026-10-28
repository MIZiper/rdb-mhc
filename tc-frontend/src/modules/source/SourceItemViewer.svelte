<script lang="ts">
    import type { ViewerProps } from "../registry";

    let { content_in }: ViewerProps = $props();
    const hasContent = $derived(
        !!content_in && typeof content_in === "object" && Object.keys(content_in).length > 0,
    );
</script>

<div class="text-secondary small border rounded p-3 bg-body-tertiary">
    <div class="fw-semibold mb-1">Source-managed item</div>
    <p class="mb-1">
        This item does not have content yet. Link it from the corresponding source
        application (DAC Web or TPL); the source will fill in the concrete type.
    </p>
    <p class="mb-0">
        If you arrived here by mistake, you can still edit the title, description,
        tags and visibility on the right.
    </p>
    {#if hasContent}
        <pre class="mt-2 mb-0 small">{JSON.stringify(content_in, null, 2)}</pre>
    {/if}
</div>
