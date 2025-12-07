<script lang="ts">
    import {
        Button,
        ButtonGroup,
        ButtonToolbar,
        Container,
    } from "@sveltestrap/sveltestrap";
    import type { Tag, Category } from "../schema";
    import { onMount } from "svelte";
    import TagsGraph from "../lib/TagsGraph.svelte";

    let { clientId }: { clientId: number } = $props();
    let categories: Category[] = $state([]);
    let tags: Tag[] = $state([]);

    let activeCategory: Category | null = $state(null);
    let selectedTag: Tag | null = $state(null);

    async function addCategory() {
        const name = window.prompt("Enter category name:", "New Category");
        if (!name) return;
        const category: Category = {
            id: null,
            name: name,
            client_id: clientId,
        };
        const res = await fetch(`/api/clients/${clientId}/categories`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(category),
        });
        if (res.ok) {
            const data = await res.json();
            categories.push(data);
        }
    }

    async function addTag() {
        if (!activeCategory) return;
        const name = window.prompt("Enter tag name:", "New Tag");
        if (!name) return;
        const tag: Tag = {
            id: null,
            name: name,
            exposed: false,
            category_id: activeCategory.id || 0,
        };
        const res = await fetch(`/api/tags?category_id=${activeCategory.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tag),
        });
        if (res.ok) {
            const data = await res.json();
            tags.push(data);
        }
    }

    async function refreshCategories() {
        const res = await fetch(`/api/clients/${clientId}/categories`);
        const data = await res.json();
        categories = data;
        if (
            activeCategory &&
            !categories.find((c: Category) => c.id === activeCategory?.id)
        ) {
            activeCategory = categories[0];
        }
    }

    async function refreshTags() {
        const res = await fetch(`/api/tags/with-parent?category_id=${activeCategory?.id}`);
        const data = await res.json();
        tags = data;
        if (selectedTag && !tags.find((t: Tag) => t.id === selectedTag?.id)) {
            selectedTag = null;
        }
    }

    $effect(() => {
        if (!activeCategory) return;
        refreshTags();
    });
    $effect(() => {
        console.log(selectedTag?.name);
    });
    onMount(refreshCategories);

    async function toggleTagExpose(tag:Tag) {
        const res = await fetch(`/api/tags/${tag.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ exposed: !tag.exposed }),
        });
        if (res.ok) {
            tag.exposed = !tag.exposed;
            return true;
        }
        return false;
    }

    async function reparentTag(fromTag:Tag, toTag: Tag) {
        const res = await fetch(`/api/tags/${fromTag.id}/parent?parent_id=${toTag.id}`, {
            method: "PATCH",
        });
        return res.ok;
    }
</script>

<Container fluid>
    <ButtonGroup>
        {#each categories as category}
            <Button
                active={category.id === activeCategory?.id}
                onclick={() => (activeCategory = category)}
            >
                {category.name}
            </Button>
        {/each}
        <Button color="primary" onclick={() => addCategory()}>
            Add Category
        </Button>
    </ButtonGroup>
    <ButtonGroup>
        <Button color="primary" onclick={() => addTag()}>Add Tag</Button>
        <Button>View All</Button>
    </ButtonGroup>
    <TagsGraph tags={tags} onSelectTag={(t: Tag | null) => (selectedTag = t)} onDblClickTag={toggleTagExpose} onReparentTag={reparentTag} />
</Container>
