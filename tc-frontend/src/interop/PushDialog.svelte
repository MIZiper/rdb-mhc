<script lang="ts">
    import {
        Badge,
        Button,
        Col,
        Icon,
        Input,
        Modal,
        ModalBody,
        ModalFooter,
        ModalHeader,
        Row,
        Tooltip,
    } from "@sveltestrap/sveltestrap";
    import { getContext } from "svelte";
    import type { ItemMeta } from "../schema";

    interface ReturnResult {
        item_id: string;
        host: string;
        mode: string;
        access_key: string;
    }

    let {
        isOpen = $bindable(true),
        node_id = null,
        append_mode = false,
        onConfirm = null,
        onCancel = null,
    }: {
        isOpen: boolean;
        node_id: string | null;
        append_mode: boolean;
        onConfirm: ((result: ReturnResult) => void) | null;
        onCancel: (() => void) | null;
    } = $props();

    let rdb_host = (getContext("rdb_host") as string) || "";
    let val_key: string = $state("");
    let res_item: ItemMeta | null = $state(null);
    let node_input_invalid: boolean = $state(false);

    function calc_access_key(cds: string[], valkey: string): string {
        return "";
    }

    function resetSelection() {
        res_item = null;
    }

    async function loadItemMeta() {
        const res = await fetch(`${rdb_host}/api/nodes/${node_id}/meta`);
        if (res.ok) {
            const data = await res.json();
            res_item = {
                title: data.title,
                description: data.description,
                id: data.id,
                update_time: data.updated_time,
                tags: [],
            };
        } else {
            node_input_invalid = true;
        }
    }
</script>

<Modal {isOpen}>
    <ModalHeader>
        Resource Item Pusher
        <Badge id="rdb-link-badge" href={`${rdb_host}/`} target="_blank">
            <Icon name="box-arrow-up-right" />
        </Badge>
        <Tooltip target="rdb-link-badge">Goto resource database</Tooltip>
    </ModalHeader>
    <ModalBody>
        <Row class="mb-2">
            {#if res_item === null}
                <Col>
                    <Input
                        type="search"
                        placeholder="Type in resource node id"
                        invalid={node_input_invalid}
                        feedback="Didn't find the resource node"
                        bind:value={node_id}
                        oninput={() => (node_input_invalid = false)}
                    />
                </Col>
                <Col xs="auto">
                    <Button onclick={loadItemMeta}>
                        <Icon name="search" />
                    </Button>
                </Col>
            {:else}
                <Col>
                    <Input value={res_item.title} disabled />
                </Col>
                <Col xs="auto">
                    <Button onclick={resetSelection}>
                        <Icon name="arrow-counterclockwise" />
                    </Button>
                </Col>
            {/if}
        </Row>
        <Input
            class="mb-2"
            placeholder="The validate key"
            bind:value={val_key}
        />
        <Input type="checkbox" bind:checked={append_mode} label="Append mode" />
    </ModalBody>
    <ModalFooter>
        <Button
            color="primary"
            disabled={!res_item}
            onclick={() => {
                if (onConfirm && node_id) {
                    onConfirm({
                        item_id: node_id,
                        host: rdb_host,
                        mode: append_mode ? "a" : "w",
                        access_key: calc_access_key([], val_key),
                    });
                }
                resetSelection();
            }}>Push</Button
        >
        <Button
            color="secondary"
            onclick={() => {
                if (onCancel) onCancel();
                resetSelection();
            }}>Cancel</Button
        >
    </ModalFooter>
</Modal>
