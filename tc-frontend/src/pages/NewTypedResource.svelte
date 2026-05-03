<script lang="ts">
    import { Col, Container, Row } from "@sveltestrap/sveltestrap";
    import { BaseProcessor, registry } from "../lib/processor";
    import NewResource from "../lib/NewResource.svelte";
    import type { ItemMeta } from "../schema";

    let selected: string | null = $state(null);
    let processor: BaseProcessor | null = $state(null);
    let editorInstance: any = $state(null);
    let saving: boolean = $state(false);
    let errorMsg: string = $state("");
    let successMsg: string = $state("");

    $effect(() => {
        if (selected) processor = registry.getProcessor(selected);
    });

    async function addResource(item: ItemMeta) {
        if (!processor?.editor || !editorInstance) {
            errorMsg = "Editor not available";
            return;
        }
        saving = true;
        errorMsg = "";
        successMsg = "";
        try {
            const content = editorInstance.getContent();
            const res = await fetch(`/api/nodes/typed`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: item.title,
                    description: item.description,
                    tag_ids: item.tags.map((e) => e.id),
                    content: content,
                    data_type: processor.type,
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                errorMsg = err.detail || "Failed to create typed resource";
            } else {
                successMsg = "Resource created successfully!";
            }
        } catch (e: any) {
            errorMsg = e.message;
        } finally {
            saving = false;
        }
    }
</script>

<Container class="my-2" fluid>
    <h4>New Typed Resource</h4>
    {#if errorMsg}
        <div class="alert alert-danger">{errorMsg}</div>
    {/if}
    {#if successMsg}
        <div class="alert alert-success">{successMsg}</div>
    {/if}
    <Row>
        <Col>
            <select bind:value={selected}>
                <option value="">Select type</option>
                {#each registry.allEditors() as { type: type_id, name }}
                    <option value={type_id}>{name}</option>
                {/each}
            </select>

            {#if processor}
                <processor.editor bind:this={editorInstance} />
            {/if}
        </Col>
        <Col xs="4">
            <NewResource onSubmit={addResource} />
        </Col>
    </Row>
</Container>
