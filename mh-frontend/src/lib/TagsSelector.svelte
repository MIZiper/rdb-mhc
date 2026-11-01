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
    import type { Category, TagMeta } from "../schema";
    import { getContext, onMount, untrack } from "svelte";

    interface Layer {
        options: TagMeta[];
        selected: number | null;
    }

    let {
        onSelect = null,
        onCancel = null,
        isOpen = true,
        initialTags = [],
        allowEmpty = false,
    }: {
        onSelect: ((tags: TagMeta[]) => void) | null;
        isOpen: boolean;
        onCancel: (() => void) | null;
        initialTags?: TagMeta[];
        allowEmpty?: boolean;
    } = $props();

    function dedupeTags(tags: TagMeta[]): TagMeta[] {
        const seen = new Set<number | string>();
        const result: TagMeta[] = [];
        for (const tag of tags) {
            const key = tag.id ?? tag.name;
            if (seen.has(key)) continue;
            seen.add(key);
            result.push(tag);
        }
        return result;
    }

    let categories: Category[] = $state([]);
    let tagLayers: Layer[] = $state([]);
    let candidateTags: TagMeta[] = $state(untrack(() => dedupeTags(initialTags)));
    let currentTag: TagMeta | null = $state(null);
    let metahub_host = (getContext("mh_host") as string) || "";

    let cacheCategoryTags: Map<number, TagMeta[]> = new Map();
    let currentTagsCache: TagMeta[] = [];

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

    function removeTag(tag: TagMeta) {
        candidateTags = candidateTags.filter((t) => t != tag);
    }

    function addTag() {
        if (
            currentTag !== null &&
            !candidateTags.some((t) => currentTag?.id === t.id)
        )
            candidateTags.push(currentTag);
    }

    onMount(async () => {
        const res = await fetch(`${metahub_host}/api/clients/all/categories`);
        const data = await res.json();
        categories = data;
    });

    async function handleCategoryChange(selectedCategoryId: number | null) {
        if (selectedCategoryId === null) {
            return;
        }
        if (!cacheCategoryTags.has(selectedCategoryId)) {
            const res = await fetch(
                `${metahub_host}/api/tags/with-parent?category_id=${selectedCategoryId}`,
            );
            const data: TagMeta[] = await res.json();
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
        <div class="d-flex flex-wrap align-items-center gap-1 mb-2">
            {#each candidateTags as tag}
                <Badge class="d-inline-flex align-items-center gap-1 pe-1">
                    {tag.name}
                    <button
                        type="button"
                        class="btn-close btn-close-white"
                        style="font-size:0.6rem;"
                        aria-label="Remove {tag.name}"
                        title="Remove"
                        onclick={() => removeTag(tag)}
                    ></button>
                </Badge>
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
                disabled={candidateTags.length === 0 && !allowEmpty}
                onclick={() => {
                    if (onSelect) onSelect(candidateTags);
                }}>Submit</Button
            >
            <Button
                color="secondary"
                onclick={() => {
                    if (onCancel) onCancel();
                }}>Cancel</Button
            >
        </ButtonGroup>
    </ModalFooter>
</Modal>
