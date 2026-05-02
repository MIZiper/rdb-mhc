<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardSubtitle,
        CardTitle,
        Input,
        ListGroup,
        ListGroupItem,
        Badge,
    } from "@sveltestrap/sveltestrap";
    import type { TagDetail } from "../schema";

    let {
        tag,
        onSave,
        onDelete,
    }: {
        tag: TagDetail | null;
        onSave: (tag: TagDetail) => Promise<void>;
        onDelete: (tag: TagDetail) => Promise<void>;
    } = $props();

    let tagName: string = $state("");
    let tagExposed: boolean = $state(false);
    let dependencies: { id: number; name: string }[] = $state([]);
    let children: number[] = $state([]);
    let childNames: Record<number, string> = $state({});
    let saving: boolean = $state(false);

    $effect(() => {
        if (tag) {
            tagName = tag.name;
            tagExposed = tag.exposed;
            dependencies = [];
            children = [];
            childNames = {};
            fetchDependencies();
            fetchChildren();
        } else {
            tagName = "";
            tagExposed = false;
            dependencies = [];
            children = [];
            childNames = {};
        }
    });

    async function fetchDependencies() {
        if (!tag || !tag.id) return;
        try {
            const depIdsRes = await fetch(
                `/api/tags/${tag.id}/dependencies`,
            );
            if (!depIdsRes.ok) return;
            const depIds: number[] = await depIdsRes.json();
            if (depIds.length > 0) {
                const namesRes = await fetch(`/api/tags/search`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(depIds),
                });
                if (namesRes.ok) {
                    const names = await namesRes.json();
                    for (const depId of depIds) {
                        const dep = names.find((t: any) => t.id === depId);
                        dependencies.push({
                            id: depId,
                            name: dep?.name || `Tag #${depId}`,
                        });
                    }
                    dependencies = dependencies;
                }
            }
        } catch (_) {}
    }

    async function fetchChildren() {
        if (!tag || !tag.id) return;
        try {
            const res = await fetch(`/api/tags/${tag.id}/children`);
            if (res.ok) {
                children = await res.json();
                if (children.length > 0) {
                    const namesRes = await fetch(`/api/tags/search`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(children),
                    });
                    if (namesRes.ok) {
                        const names = await namesRes.json();
                        for (const t of names) {
                            childNames[t.id] = t.name;
                        }
                        childNames = childNames;
                    }
                }
            }
        } catch (_) {}
    }

    async function handleSave() {
        if (!tag || !tag.id || saving) return;
        saving = true;
        tag.name = tagName;
        tag.exposed = tagExposed;
        await onSave(tag);
        saving = false;
    }
</script>

<Card>
    <CardHeader>
        <CardTitle>Tag Info</CardTitle>
    </CardHeader>
    <CardBody>
        {#if tag}
            <CardSubtitle>
                <Input type="text" bind:value={tagName} />
            </CardSubtitle>
            <Input
                type="checkbox"
                bind:checked={tagExposed}
                label="Exposed"
            />
            <div class="mt-3">
                <strong>ID: </strong>{tag.id}
            </div>
            <div class="mt-1">
                <strong>Category ID: </strong>{tag.category_id}
            </div>
            {#if dependencies.length > 0}
                <div class="mt-2">
                    <strong>Dependencies:</strong>
                    <ListGroup flush class="mt-1">
                        {#each dependencies as dep}
                            <ListGroupItem
                                ><Badge>{dep.name}</Badge></ListGroupItem
                            >
                        {/each}
                    </ListGroup>
                </div>
            {/if}
            <div class="mt-2">
                <strong>Children ({children.length}):</strong>
                {#if children.length > 0}
                    <div class="mt-1">
                        {#each children as childId}
                            <Badge class="me-1"
                                >{childNames[childId] || `#${childId}`}</Badge
                            >
                        {/each}
                    </div>
                {:else}
                    <span class="text-muted"> No children</span>
                {/if}
            </div>
        {:else}
            Click on a tag node to view properties.
        {/if}
    </CardBody>
    {#if tag}
        <CardFooter class="d-flex justify-content-between">
            <Button
                color="primary"
                onclick={handleSave}
                disabled={saving}
            >
                {saving ? "Saving..." : "Save"}
            </Button>
            <Button color="danger" onclick={() => onDelete(tag!)}>
                Delete Tag
            </Button>
        </CardFooter>
    {/if}
</Card>
