<script lang="ts">
    import { Badge, Card, CardBody } from "@sveltestrap/sveltestrap";
    import { sourceSystemLabel } from "../lib/utils/ui";

    let {
        sourceSystem,
        sourcePart,
        sourceUrl,
        frozen = false,
    }: {
        sourceSystem: string | null;
        sourcePart?: string | null;
        sourceUrl?: string | null;
        frozen?: boolean;
    } = $props();
</script>

<Card class="shadow-sm mb-3 border-0 bg-body-tertiary">
    <CardBody class="small py-2 px-3">
        <div class="d-flex flex-wrap align-items-center gap-2">
            <span class="fw-semibold">Managed by source</span>
            <Badge class="text-bg-secondary">{sourceSystemLabel(sourceSystem)}</Badge>
            {#if frozen}
                <Badge class="text-bg-warning">Frozen</Badge>
            {/if}
            {#if sourcePart}
                <span class="d-inline-flex align-items-center gap-1">
                    <span class="text-secondary">Part</span>
                    <Badge class="bg-secondary-subtle text-secondary-emphasis border">{sourcePart}</Badge>
                </span>
            {/if}
            {#if sourceUrl}
                <a class="ms-auto" href={sourceUrl} target="_blank" rel="noreferrer">
                    Open in {sourceSystemLabel(sourceSystem)}
                </a>
            {/if}
        </div>
        <div class="text-secondary mt-1">
            Title, description, tags and status are managed in TC. Content is
            managed by {sourceSystemLabel(sourceSystem)}. Use the source
            application to view or change it.
        </div>
    </CardBody>
</Card>
