<script lang="ts">
    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import {
        Button,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardTitle,
        Col,
        Container,
        Input,
        Label,
        Row,
    } from "@sveltestrap/sveltestrap";
    import type { ItemMeta } from "../schema";

    let item: ItemMeta = $state({
        title: "",
        description: "",
        id: null,
        update_time: new Date(),
        tags: [],
        data_type: "",
    });
    let tagSelectorOpen: boolean = $state(false);

    let { onSubmit } = $props();

    function useTags(_tags: TagMeta[]) {
        if (item) {
            item.tags = _tags;
        }
        tagSelectorOpen = false;
    }

    let saving = $state(false);
    let errorMsg = $state("");

    async function addResource() {
        saving = true;
        errorMsg = "";
        try {
            const res = await fetch(`/api/nodes/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: item.title,
                    description: item.description,
                    tag_ids: item.tags.map((e) => e.id),
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                errorMsg = err.detail || "Failed to create resource";
            } else {
                item.title = "";
                item.description = "";
                item.tags = [];
            }
        } catch (e: any) {
            errorMsg = e.message;
        } finally {
            saving = false;
        }
    }
</script>

<Card>
    <CardHeader>
        <CardTitle>New Resource</CardTitle>
    </CardHeader>
    <CardBody>
        <Label>Title</Label>
        <Input type="text" bind:value={item.title} />
        <Label>Description</Label>
        <Input type="textarea" bind:value={item.description} />

        <Button
            class="mt-4"
            onclick={() => {
                tagSelectorOpen = true;
            }}>Edit Tags</Button
        >
        <p>
            <i>Tags:</i>
            <span>{item.tags.map((e) => e.name).join(", ")}</span>
            <br />
            <i>TagsStr:</i>
            <span>{item.tags.map((e) => e.id).join(";")}</span>
        </p>
    </CardBody>
    <CardFooter>
        {#if errorMsg}
            <div class="text-danger mb-2">{errorMsg}</div>
        {/if}
        <Button
            color="primary"
            disabled={saving}
            onclick={() => {
                if (onSubmit) onSubmit(item);
                else addResource();
            }}>{saving ? "Saving..." : "Add Resource"}</Button
        >
    </CardFooter>
</Card>

<TagsSelector
    isOpen={tagSelectorOpen}
    onSelect={useTags}
    onCancel={() => {
        tagSelectorOpen = false;
    }}
/>
