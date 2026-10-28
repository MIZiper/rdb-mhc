<script lang="ts">
    import { Badge, Card, CardBody, CardHeader } from "@sveltestrap/sveltestrap";
    import type { NodeContribution } from "../types";
    import { sourceSystemLabel } from "../lib/utils/ui";

    let { contributions }: { contributions: NodeContribution[] } = $props();

    function formatDate(value: string): string {
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
    }
</script>

<Card class="shadow-sm mb-3">
    <CardHeader class="fw-semibold">
        Contributions ({contributions.length})
    </CardHeader>
    <CardBody class="small">
        {#if contributions.length === 0}
            <span class="text-muted">No external contributions</span>
        {:else}
            <ul class="list-unstyled mb-0 d-flex flex-column gap-2">
                {#each contributions as contribution}
                    <li>
                        <div class="d-flex flex-wrap align-items-center gap-2">
                            {#if contribution.source_url}
                                <a href={contribution.source_url} target="_blank" rel="noreferrer">
                                    {sourceSystemLabel(contribution.source_system)}
                                    {#if contribution.source_part}/{contribution.source_part}{/if}
                                </a>
                            {:else}
                                <span>
                                    {sourceSystemLabel(contribution.source_system)}
                                    {#if contribution.source_part}/{contribution.source_part}{/if}
                                </span>
                            {/if}
                            {#if contribution.contributed_type}
                                <Badge class="text-bg-secondary">{contribution.contributed_type}</Badge>
                            {/if}
                            <Badge class="text-bg-light text-dark">mode {contribution.mode}</Badge>
                            {#if contribution.push_count > 1}
                                <Badge class="text-bg-info">×{contribution.push_count}</Badge>
                            {/if}
                        </div>
                        <div class="text-secondary">
                            {formatDate(contribution.pushed_at)}
                            {#if contribution.pushed_by}· {contribution.pushed_by}{/if}
                        </div>
                    </li>
                {/each}
            </ul>
        {/if}
    </CardBody>
</Card>
