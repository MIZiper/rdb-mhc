<script lang="ts">
    import {
        Button,
        ButtonGroup,
        ButtonToolbar,
        Container,
    } from "@sveltestrap/sveltestrap";
    import type { Tag, Category } from "../schema";

    let categories: Category[] = [
        { id: 1, name: "ScopeA" },
        { id: 2, name: "ScopeB" },
        { id: 3, name: "ScopeC" },
    ];

    let activeCategory: number = $state(2);

    async function addCategory() {}

    async function addTag() {}
</script>

<Container fluid>
    <ButtonGroup>
        {#each categories as category}
            <Button
                active={category.id === activeCategory}
                onclick={() => (activeCategory = category.id)}
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
</Container>
