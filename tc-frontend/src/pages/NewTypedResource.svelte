<script lang="ts">
    import { Col, Container, Input, Label, Row } from "@sveltestrap/sveltestrap";
    import { getContext } from "svelte";
    import { searchParams } from "sv-router";
    import { BaseProcessor, registry } from "../modules/registry";
    import NewResource from "../components/NewResource.svelte";
    import type { ItemMeta } from "../types";
    import { authFetch, isAuthenticated } from "../lib/auth";

    const router: any = getContext("router");

    let selected: string | null = $state(null);
    let processor: BaseProcessor | null = $state(null);
    let editorInstance: any = $state(null);
    let saving: boolean = $state(false);
    let errorMsg: string = $state("");
    let successMsg: string = $state("");
    let initialized: boolean = $state(false);

    $effect(() => {
        if (selected) processor = registry.getProcessor(selected);
        else processor = null;
    });

    $effect(() => {
        if (initialized) return;
        initialized = true;
        const requested = String(searchParams.get("type") || "");
        if (requested) {
            const candidate = registry.getProcessor(requested);
            if (candidate?.creatable) selected = requested;
        }
    });

    async function addResource(item: ItemMeta) {
        if (!isAuthenticated()) {
            errorMsg = "Please login to create resources";
            return;
        }
        if (!processor) {
            errorMsg = "Select a type first";
            return;
        }
        if (processor.editor && !editorInstance) {
            errorMsg = "Editor not available";
            return;
        }
        saving = true;
        errorMsg = "";
        successMsg = "";
        try {
            const content = processor.editor ? editorInstance.getContent() : {};
            const res = await authFetch(`/api/nodes/typed`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: item.title,
                    description: item.description,
                    tag_ids: item.tags.map((e) => e.id),
                    visibility: item.visibility,
                    content: content,
                    data_type: processor.type,
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                errorMsg = err.detail || "Failed to create typed resource";
            } else {
                const data = await res.json();
                router.navigate(`/items/${data.id}`);
            }
        } catch (e: any) {
            errorMsg = e.message;
        } finally {
            saving = false;
        }
    }
</script>

<Container class="my-2" fluid>
    <h4>New Resource</h4>
    {#if errorMsg}
        <div class="alert alert-danger">{errorMsg}</div>
    {/if}
    {#if successMsg}
        <div class="alert alert-success">{successMsg}</div>
    {/if}
    <Row>
        <Col>
            <Label>Type</Label>
            <Input type="select" bind:value={selected}>
                <option value="">Select type</option>
                {#each registry.allCreatable() as { type: type_id, name }}
                    <option value={type_id}>{name}</option>
                {/each}
            </Input>

            {#if processor}
                {#if processor.editor}
                    <processor.editor bind:this={editorInstance} />
                {:else}
                    <div class="alert alert-info mt-3 mb-0 small">
                        <strong>{processor.name}</strong> has no content editor.
                        Create it here, then link it from DAC Web or TPL; the
                        source application will fill in its concrete type.
                    </div>
                {/if}
            {/if}
        </Col>
        <Col xs="4">
            <NewResource onSubmit={addResource} />
        </Col>
    </Row>
</Container>
