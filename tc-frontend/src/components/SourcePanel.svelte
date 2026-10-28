<script lang="ts">
    import { Badge, Card, CardBody, CardHeader } from "@sveltestrap/sveltestrap";
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

<Card class="shadow-sm mb-3">
    <CardHeader class="fw-semibold d-flex align-items-center gap-2">
        <span>Managed by source</span>
        <Badge class="text-bg-secondary">{sourceSystemLabel(sourceSystem)}</Badge>
        {#if frozen}
            <Badge class="text-bg-warning">Frozen</Badge>
        {/if}
    </CardHeader>
    <CardBody class="small">
        <p class="mb-2 text-secondary">
            Title, description, tags and status are managed in TC. Content is
            controlled by the source application.
        </p>
        <dl class="row mb-2">
            <dt class="col-4 fw-normal text-secondary">System</dt>
            <dd class="col-8 mb-1">{sourceSystemLabel(sourceSystem)}</dd>
            {#if sourcePart}
                <dt class="col-4 fw-normal text-secondary">Part</dt>
                <dd class="col-8 mb-1">{sourcePart}</dd>
            {/if}
        </dl>
        {#if sourceUrl}
            <a href={sourceUrl} target="_blank" rel="noreferrer">
                Open in {sourceSystemLabel(sourceSystem)}
            </a>
        {/if}
    </CardBody>
</Card>
