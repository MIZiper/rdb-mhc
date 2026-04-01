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
    });
    let tagSelectorOpen: boolean = $state(false);

    function useTags(_tags: TagMeta[]) {
        if (item) {
            item.tags = _tags;
        }
        tagSelectorOpen = false;
    }

    async function addResource() {
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
        <Button color="primary" onclick={addResource}>Add Resource</Button>
    </CardFooter>
</Card>

<TagsSelector
    isOpen={tagSelectorOpen}
    onSelect={useTags}
    onCancel={() => {
        tagSelectorOpen = false;
    }}
/>
