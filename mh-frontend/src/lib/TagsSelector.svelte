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
    import { onMount } from "svelte";

    interface Layer {
        options: Tag[];
        selected: number | null;
    }

    let {
        onSelect,
        isOpen = true,
    }: { onSelect: (tags: Tag[]) => void; isOpen: boolean } = $props();

    let categories: Category[] = $state([]);
    let tagLayers: Layer[] = $state([]);
    let candidateTags: Tag[] = $state([]);
    let currentTag: Tag | null = $state(null);

    let cacheCategoryTags: Map<number, Tag[]> = new Map();
    let currentTagsCache: Tag[] = [];

    function refreshCurrentTag() {
        for (let i = tagLayers.length - 1; i >= 0; i--) {
            if (tagLayers[i].selected !== null) {
                const selectedLayer = tagLayers[i];
                const selectedTag = selectedLayer.options.find(
                    (t) => t.id === selectedLayer.selected,
                );
                if (selectedTag === undefined) {
                    // error, mismatch on layer.selected
                    return null;
                }
                return selectedTag;
            }
        }
        return null;
    }

    function removeTag(tag: Tag) {
        candidateTags = candidateTags.filter((t) => t != tag);
    }

    function submitTags() {
        onSelect(candidateTags);
    }

    function addTag() {
        if (currentTag !== null && !candidateTags.some((t) => currentTag?.id === t.id))
            candidateTags.push(currentTag);
    }

    onMount(async () => {
        const res = await fetch(`/api/clients/all/categories`);
        const data = await res.json();
        categories = data;
    });

    async function handleCategoryChange(selectedCategoryId: number | null) {
        if (selectedCategoryId === null) {
            return;
        }
        if (!cacheCategoryTags.has(selectedCategoryId)) {
            const res = await fetch(
                `/api/tags/with-parent?category_id=${selectedCategoryId}`,
            );
            const data: Tag[] = await res.json();
            cacheCategoryTags.set(selectedCategoryId, data);
        }
        let data = cacheCategoryTags.get(selectedCategoryId);
        if (data !== undefined) {
            currentTagsCache = data;
            tagLayers = [
                {
                    options: data.filter((t) => t.parent_id === null),
                    selected: null,
                },
            ];
        } else {
            tagLayers = [];
        }

        currentTag = refreshCurrentTag();
    }

    async function handleTagChange(idx: number, selectedTagId: number | null) {
        tagLayers[idx].selected = selectedTagId;
        tagLayers = tagLayers.slice(0, idx + 1);

        if (selectedTagId !== null) {
            const children = currentTagsCache.filter(
                (t) => t.parent_id === selectedTagId,
            );
            if (children.length > 0) {
                tagLayers.push({ options: children, selected: null });
            }
        }

        currentTag = refreshCurrentTag();
    }
</script>

<Modal {isOpen}>
    <ModalHeader>Tags selector</ModalHeader>

    <ModalBody>
        <div class="mb-2">
            {#each candidateTags as tag}
                <Badge class="me-1" ondblclick={() => removeTag(tag)}>{tag.name}</Badge>
            {/each}
        </div>
        <FormGroup>
            <Input
                type="select"
                onchange={(e) =>
                    handleCategoryChange(Number(e.currentTarget.value) || null)}
            >
                <option value="" disabled selected>Select category</option>
                {#each categories as category}
                    <option value={category.id}>{category.name}</option>
                {/each}
            </Input>

            {#each tagLayers as tagLayer, idx}
                <Input
                    class="mt-2"
                    type="select"
                    onchange={(e) =>
                        handleTagChange(
                            idx,
                            Number(e.currentTarget.value) || null,
                        )}
                >
                    {#if idx == 0}
                        <option value="" selected disabled>Select tag</option>
                    {:else}
                        <option value="" selected
                            >(Optional) select child tag</option
                        >
                    {/if}
                    {#each tagLayer.options as tag}
                        <option value={tag.id}>{tag.name}</option>
                    {/each}
                </Input>
            {/each}
        </FormGroup>
    </ModalBody>
    <ModalFooter>
        <Button color="info" disabled={currentTag === null} onclick={addTag}
            >Add Tag</Button
        >
        <ButtonGroup>
            <Button
                color="primary"
                disabled={candidateTags.length === 0}
                onclick={submitTags}>Submit</Button
            >
            <Button color="secondary">Cancel</Button>
        </ButtonGroup>
    </ModalFooter>
</Modal>
