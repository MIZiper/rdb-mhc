<script lang="ts">
    import {
        Input,
        Modal,
        ModalBody,
        ModalHeader,
    } from "@sveltestrap/sveltestrap";
    import { getContext } from "svelte";

    let { credentials } = $props();
    let rdb_host = (getContext("rdb_host") as string) || "";

    function calc_access_key(cds: string[], psd: string) {}
</script>

<Modal>
    <ModalHeader>Push to DB</ModalHeader>
    <ModalBody>
        <Input placeholder="Node id" />
        <Input placeholder="The validate password" />
        <Input type="checkbox" label="Append?" />
    </ModalBody>
</Modal>
