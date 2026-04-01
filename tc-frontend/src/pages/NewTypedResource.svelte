<script lang="ts">
    import { Col, Container, Row } from "@sveltestrap/sveltestrap";
    import { BaseProcessor, registry } from "../lib/processor";
    import NewResource from "../lib/NewResource.svelte";

    let selected: string | null = $state(null);
    let processor: BaseProcessor | null = $state(null);

    $effect(() => {
        if (selected) processor = registry.getProcessor(selected);
    });
</script>

<Container class="my-2" fluid>
    <Row>
        <Col>
            <select bind:value={selected}>
                {#each registry.allProcessors() as { type: type_id, name }}
                    <option value={type_id}>{name}</option>
                {/each}
            </select>

            {#if processor}
                <processor.editor />
            {/if}
        </Col>
        <Col xs="4">
            <NewResource />
        </Col>
    </Row>
</Container>
