<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        CardSubtitle,
        Col,
        Container,
        FormGroup,
        Input,
        Label,
        Modal,
        ModalBody,
        ModalFooter,
        ModalHeader,
        Row,
        Spinner,
    } from "@sveltestrap/sveltestrap";
    import type { Client, Category } from "../schema";
    import { onMount } from "svelte";

    let clients: Client[] = $state([]);
    let categories: Category[] = $state([]);
    let loading: boolean = $state(true);
    let isModalOpen: boolean = $state(false);
    let editClient: Client | null = $state(null);
    let newName: string = $state("");
    let newHost: string = $state("");

    async function fetchClients() {
        loading = true;
        const res = await fetch("/api/clients");
        if (res.ok) {
            clients = await res.json();
        }
        loading = false;
    }

    async function fetchCategories() {
        const res = await fetch("/api/clients/all/categories");
        if (res.ok) {
            categories = await res.json();
        }
    }

    function openCreateModal() {
        editClient = null;
        newName = "";
        newHost = "";
        isModalOpen = true;
    }

    function closeModal() {
        isModalOpen = false;
        editClient = null;
    }

    async function handleSubmit() {
        if (!newName) return;
        const body = { name: newName, host: newHost || null };
        const res = await fetch("/api/clients", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (res.ok) {
            closeModal();
            fetchClients();
        } else {
            const err = await res.json().catch(() => ({}));
            alert(err.detail || "Failed to register client");
        }
    }

    async function handleDelete(clientId: number) {
        if (!confirm("Delete this client and all its categories/tags?")) return;
        const res = await fetch(`/api/clients/${clientId}`, {
            method: "DELETE",
        });
        if (res.ok) {
            fetchClients();
        } else {
            alert("Failed to delete client");
        }
    }

    function getCategoryCount(clientId: number | null): number {
        return categories.filter((c) => c.client_id === clientId).length;
    }

    onMount(() => {
        fetchClients();
        fetchCategories();
    });
</script>

<Container fluid class="mt-2">
    <Row class="mb-3 align-items-center">
        <Col>
            <h4>Clients</h4>
        </Col>
        <Col class="text-end">
            <Button color="primary" onclick={openCreateModal}>
                Register Client
            </Button>
        </Col>
    </Row>

    {#if loading}
        <div class="text-center py-5">
            <Spinner />
        </div>
    {:else if clients.length === 0}
        <p class="text-muted">
            No clients registered. Register a new client to start.
        </p>
    {:else}
        <Row>
            {#each clients as client}
                <Col md="6" lg="4" class="mb-3">
                    <Card>
                        <CardHeader>
                            <CardTitle>{client.name}</CardTitle>
                            <CardSubtitle>
                                {getCategoryCount(client.id)} categories
                            </CardSubtitle>
                        </CardHeader>
                        <CardBody>
                            {#if client.host}
                                <div class="mb-1">
                                    <strong>TC Host: </strong>{client.host}
                                </div>
                            {:else}
                                <div class="mb-1 text-muted">
                                    No downstream host configured
                                </div>
                            {/if}
                        </CardBody>
                        <div class="card-footer d-flex justify-content-end gap-2">
                            <Button
                                color="info"
                                size="sm"
                                href={`/admin/${client.id}`}
                            >
                                Manage Tags
                            </Button>
                            <Button
                                color="danger"
                                size="sm"
                                onclick={() => handleDelete(client.id!)}
                            >
                                Delete
                            </Button>
                        </div>
                    </Card>
                </Col>
            {/each}
        </Row>
    {/if}
</Container>

<Modal isOpen={isModalOpen} toggle={closeModal}>
    <ModalHeader>Register New Client</ModalHeader>
    <ModalBody>
        <FormGroup>
            <Label>Client Name</Label>
            <Input type="text" placeholder="My Client" bind:value={newName} />
        </FormGroup>
        <FormGroup>
            <Label>Downstream TC Host (optional)</Label>
            <Input
                type="text"
                placeholder="localhost:8030"
                bind:value={newHost}
            />
        </FormGroup>
    </ModalBody>
    <ModalFooter>
        <Button color="primary" disabled={!newName} onclick={handleSubmit}>
            Register
        </Button>
        <Button color="secondary" onclick={closeModal}>Cancel</Button>
    </ModalFooter>
</Modal>
