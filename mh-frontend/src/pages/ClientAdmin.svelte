<script lang="ts">
    import {
        Button,
        ButtonGroup,
        ButtonToolbar,
        Col,
        Container,
        Row,
    } from "@sveltestrap/sveltestrap";
    import type { TagDetail, Category } from "../schema";
    import { getContext, onMount } from "svelte";
    import TagsGraph from "../lib/TagsGraph.svelte";
    import TagInfo from "../lib/TagInfo.svelte";

    const router = getContext("router");
    router.route.getParams("/admin/:id");

    const clientId = Number(router.route.params.id);
    let categories: Category[] = $state([]);
    let tags: TagDetail[] = $state([]);

    let activeCategory: Category | null = $state(null);
    let selectedTag: TagDetail | null = $state(null);

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
        const tag: TagDetail = {
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
        const res = await fetch(
            `/api/tags/with-parent?category_id=${activeCategory?.id}`,
        );
        const data = await res.json();
        tags = data;
        if (selectedTag && !tags.find((t: TagDetail) => t.id === selectedTag?.id)) {
            selectedTag = null;
        }
    }

    $effect(() => {
        if (!activeCategory) return;
        refreshTags();
    });
    onMount(refreshCategories);

    async function toggleTagExpose(tag: TagDetail) {
        const res = await fetch(`/api/tags/${tag.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ exposed: !tag.exposed, name: tag.name }),
        });
        if (res.ok) {
            tag.exposed = !tag.exposed;
            return true;
        }
        return false;
    }

    async function reparentTag(fromTag: TagDetail, toTag: TagDetail) {
        const res = await fetch(
            `/api/tags/${fromTag.id}/parent?parent_id=${toTag.id}`,
            {
                method: "PATCH",
            },
        );
        if (res.ok) {
            fromTag.parent_id = toTag.id;
        }
        return res.ok;
    }

    async function handleSaveTag(tag: TagDetail) {
        const res = await fetch(`/api/tags/${tag.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ exposed: tag.exposed, name: tag.name }),
        });
        if (res.ok) {
            refreshTags();
        } else {
            alert("Failed to save tag");
        }
    }

    async function handleDeleteTag(tag: TagDetail) {
        if (!confirm(`Delete tag "${tag.name}" and all its relationships?`)) return;
        const res = await fetch(`/api/tags/${tag.id}`, { method: "DELETE" });
        if (res.ok) {
            selectedTag = null;
            refreshTags();
        } else {
            alert("Failed to delete tag");
        }
    }

    async function renameCategory() {
        if (!activeCategory) return;
        const name = window.prompt("New category name:", activeCategory.name);
        if (!name) return;
        const res = await fetch(
            `/api/clients/${clientId}/categories/${activeCategory.id}`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name }),
            },
        );
        if (res.ok) {
            activeCategory.name = name;
            categories = [...categories];
        } else {
            alert("Failed to rename category");
        }
    }

    async function deleteCategory() {
        if (!activeCategory) return;
        if (!confirm(`Delete category "${activeCategory.name}" and all its tags?`))
            return;
        const res = await fetch(
            `/api/clients/${clientId}/categories/${activeCategory.id}`,
            { method: "DELETE" },
        );
        if (res.ok) {
            activeCategory = null;
            selectedTag = null;
            refreshCategories();
        } else {
            alert("Failed to delete category");
        }
    }
</script>

<Container class="mt-2" fluid>
    <div class="d-flex align-items-center gap-2 mb-2">
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
                + Category
            </Button>
        </ButtonGroup>
        {#if activeCategory}
            <Button color="warning" size="sm" onclick={renameCategory}>
                Rename
            </Button>
            <Button color="danger" size="sm" onclick={deleteCategory}>
                Delete
            </Button>
        {/if}
        <ButtonGroup>
            <Button color="success" onclick={() => addTag()}>+ Tag</Button>
            <Button href="/clients">All Clients</Button>
        </ButtonGroup>
    </div>
    <Row class="mt-2">
        <Col>
            <TagsGraph
                {tags}
                onSelectTag={(t: TagDetail | null) => (selectedTag = t)}
                onDblClickTag={toggleTagExpose}
                onReparentTag={reparentTag}
            />
        </Col>
        <Col>
            <TagInfo
                tag={selectedTag}
                onSave={handleSaveTag}
                onDelete={handleDeleteTag}
            />
        </Col>
    </Row>
</Container>
