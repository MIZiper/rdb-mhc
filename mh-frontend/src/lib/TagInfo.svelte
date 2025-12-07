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
    } from "@sveltestrap/sveltestrap";
    import type { Tag } from "../schema";

    let { tag }: { tag: Tag | null } = $props();
</script>

<Card>
    <CardHeader>
        <CardTitle>Tag Info</CardTitle>
    </CardHeader>
    <CardBody>
        {#if tag}
            <CardSubtitle>{tag.name}</CardSubtitle>
            <Input
                type="checkbox"
                disabled
                checked={tag.exposed}
                label="Exposed"
            />
            <ListGroup>
                <ListGroupItem>Dependency 1</ListGroupItem>
                <ListGroupItem>Dependency 2</ListGroupItem>
                <ListGroupItem>Dependency ...</ListGroupItem>
            </ListGroup>
        {:else}
            Click on a tag node to view properties.
        {/if}
    </CardBody>
    {#if tag}
        <CardFooter>
            <Button>Save</Button>
        </CardFooter>
    {/if}
</Card>
