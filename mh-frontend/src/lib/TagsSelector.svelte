<script lang="ts">
    import {
        Badge,
        Button,
        ButtonGroup,
        FormGroup,
        Input,
        Modal,
        ModalBody,
        ModalFooter,
        ModalHeader,
    } from "@sveltestrap/sveltestrap";
    import type { Category, Tag } from "../schema";

    interface Layer {
        options: Tag[];
        selected: number;
    }

    let categories: Category[] = $state([]);
    let selectedCategory: Category | null = $state(null);
    let tagLayers: Layer[] = $state([]);
    let selectedTags: Tag[] = $state([]);
</script>

<Modal isOpen={true}>
    <ModalHeader>Tags selector</ModalHeader>

    <ModalBody>
        <div>
            {#each selectedTags as tag}
                <Badge>{tag.name}</Badge>
            {/each}
        </div>
        <FormGroup>
            <Input type="select">
                <option value="" disabled selected>Select category</option>
                {#each categories as category}
                    <option value={category.id}>{category.name}</option>
                {/each}
            </Input>

            {#each tagLayers as tagLayer}
                <Input type="select">
                    <option value="" disabled selected>Select tag</option>
                    {#each tagLayer.options as tag}
                        <option value={tag.id}>{tag.name}</option>
                    {/each}
                </Input>
            {/each}
        </FormGroup>
    </ModalBody>
    <ModalFooter>
        <Button color="info">Add Tag</Button>
        <ButtonGroup>
            <Button color="primary">Submit</Button>
            <Button color="secondary">Cancel</Button>
        </ButtonGroup>
    </ModalFooter>
</Modal>
