<script lang="ts">
    import { Button, Col, Input, Row } from "@sveltestrap/sveltestrap";
    import { getContext } from "svelte";

    let { onSearch }: { onSearch: (query: string) => void } = $props();
    let query: string = $state("");

    function handleSearch() {
        if (onSearch) onSearch(query.trim());
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Enter") handleSearch();
    }
</script>

<Row>
    <Col>
        <Input
            type="search"
            placeholder="Tags or content"
            bind:value={query}
            onkeypress={handleKeydown}
        />
    </Col>
    <Col xs="auto">
        <Button onclick={handleSearch}>Search</Button>
    </Col>
</Row>
