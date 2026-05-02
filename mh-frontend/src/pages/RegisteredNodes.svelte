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
        ListGroup,
        ListGroupItem,
        Modal,
        ModalBody,
        ModalFooter,
        ModalHeader,
        Row,
        Spinner,
        Badge,
    } from "@sveltestrap/sveltestrap";
    import type {
        NodeRegistration,
        NodeRegistrationList,
        Client,
        Category,
        TagMeta,
        TagDescendant,
    } from "../schema";
    import { onMount } from "svelte";

    let registrations: NodeRegistration[] = $state([]);
    let clients: Client[] = $state([]);
    let categories: Category[] = $state([]);
    let total: number = $state(0);
    let loading: boolean = $state(true);
    let filterClientId: number | null = $state(null);
    let tagNames: Record<number, string> = $state({});

    let isModalOpen: boolean = $state(false);
    let editReg: NodeRegistration | null = $state(null);

    let newClientId: number = $state(0);
    let newNodeId: string = $state("");
    let newDescription: string = $state("");
    let newLink: string = $state("");
    let newNodeTagIds: string = $state("");
    let selectedTagId: number | null = $state(null);

    let availableTags: TagMeta[] = $state([]);
    let allCategories: Category[] = $state([]);

    async function fetchRegistrations() {
        loading = true;
        let url = "/api/nodes/";
        if (filterClientId) {
            url += `?client_id=${filterClientId}`;
        }
        const res = await fetch(url);
        if (res.ok) {
            const data: NodeRegistrationList = await res.json();
            registrations = data.items;
            total = data.total;
            await fetchAllTagNames(data.items);
        }
        loading = false;
    }

    async function fetchAllTagNames(items: NodeRegistration[]) {
        const allTagIds = new Set<number>();
        for (const item of items) {
            allTagIds.add(item.tag_id);
            for (const tid of item.node_tag_ids) {
                allTagIds.add(tid);
            }
        }
        if (allTagIds.size > 0) {
            const res = await fetch("/api/tags/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify([...allTagIds]),
            });
            if (res.ok) {
                const data = await res.json();
                for (const t of data) {
                    tagNames[t.id] = t.name;
                }
                tagNames = tagNames;
            }
        }
    }

    async function fetchClients() {
        const res = await fetch("/api/clients");
        if (res.ok) {
            clients = await res.json();
        }
    }

    async function fetchCategories() {
        const res = await fetch("/api/clients/all/categories");
        if (res.ok) {
            allCategories = await res.json();
        }
    }

    async function fetchTagsForCategory(categoryId: number) {
        const res = await fetch(
            `/api/tags/with-parent?category_id=${categoryId}`,
        );
        if (res.ok) {
            availableTags = await res.json();
        }
    }

    function openRegisterModal() {
        isModalOpen = true;
        editReg = null;
        newClientId = clients[0]?.id || 0;
        newNodeId = "";
        newDescription = "";
        newLink = "";
        newNodeTagIds = "";
        selectedTagId = null;
    }

    function openEditModal(reg: NodeRegistration) {
        isModalOpen = true;
        editReg = reg;
        newClientId = reg.client_id;
        newNodeId = reg.client_node_id;
        newDescription = (reg.params?.description as string) || "";
        newLink = (reg.params?.link as string) || "";
        newNodeTagIds = reg.node_tag_ids.join(",");
        selectedTagId = reg.tag_id;
    }

    function closeModal() {
        isModalOpen = false;
        editReg = null;
    }

    async function handleSubmit() {
        if (!selectedTagId) return;

        const body = {
            tag_id: selectedTagId,
            client_id: newClientId,
            client_node_id: newNodeId,
            node_tag_ids: newNodeTagIds
                ? newNodeTagIds.split(",").map((s) => parseInt(s.trim()))
                : [],
            description: newDescription || null,
            link: newLink || null,
        };

        if (editReg) {
            const res = await fetch(`/api/nodes/${editReg.tag_id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            if (res.ok) {
                closeModal();
                fetchRegistrations();
            } else {
                alert("Failed to update registration");
            }
        } else {
            const res = await fetch("/api/nodes/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            if (res.ok) {
                closeModal();
                fetchRegistrations();
            } else {
                const err = await res.json().catch(() => ({}));
                alert(
                    (err.detail as string) ||
                        "Failed to create registration. A node may already be registered for this tag.",
                );
            }
        }
    }

    async function handleDelete(tagId: number) {
        if (!confirm("Are you sure you want to delete this node registration?"))
            return;
        const res = await fetch(`/api/nodes/${tagId}`, { method: "DELETE" });
        if (res.ok) {
            fetchRegistrations();
        } else {
            alert("Failed to delete node registration.");
        }
    }

    $effect(() => {
        fetchRegistrations();
    });

    onMount(() => {
        fetchClients();
        fetchCategories();
    });
</script>

<Container fluid class="mt-2">
    <Row class="mb-3 align-items-center">
        <Col>
            <h4>Registered Nodes ({total})</h4>
        </Col>
        <Col class="text-end">
            <FormGroup class="d-inline-block me-2">
                <Input
                    type="select"
                    onchange={(e) => {
                        filterClientId = Number(e.currentTarget.value) || null;
                        fetchRegistrations();
                    }}
                >
                    <option value="">All Clients</option>
                    {#each clients as client}
                        <option value={client.id}>{client.name}</option>
                    {/each}
                </Input>
            </FormGroup>
            <Button color="primary" onclick={openRegisterModal}>
                Register Node
            </Button>
        </Col>
    </Row>

    {#if loading}
        <div class="text-center py-5">
            <Spinner />
        </div>
    {:else if registrations.length === 0}
        <p class="text-muted">No registered nodes found.</p>
    {:else}
        <Row>
            {#each registrations as reg}
                <Col md="6" lg="4" class="mb-3">
                    <Card>
                        <CardHeader>
                            <CardTitle>
                                Tag:
                                {tagNames[reg.tag_id] || `#${reg.tag_id}`}
                            </CardTitle>
                            <CardSubtitle>
                                {clients.find((c) => c.id === reg.client_id)
                                    ?.name || `Client #${reg.client_id}`}
                            </CardSubtitle>
                        </CardHeader>
                        <CardBody>
                            <div class="mb-1">
                                <strong>Node:
                                </strong>{reg.client_node_id.substring(0, 8)}...
                            </div>
                            {#if reg.params?.description}
                                <div class="mb-1">
                                    <strong>Description:
                                    </strong>{reg.params.description}
                                </div>
                            {/if}
                            {#if reg.params?.link}
                                <div class="mb-1">
                                    <strong>Link:
                                    </strong><a
                                        href={reg.params.link}
                                        target="_blank"
                                        >{reg.params.link}</a
                                    >
                                </div>
                            {/if}
                            {#if reg.client_id && clients.find((c) => c.id === reg.client_id)?.host}
                                <div class="mb-1">
                                    <strong>TC Host:
                                    </strong>{clients.find((c) => c.id === reg.client_id)?.host}
                                </div>
                            {/if}
                            <div class="mt-2">
                                <strong>Bound Tags: </strong>
                                {#each reg.node_tag_ids as tid}
                                    <Badge class="me-1"
                                        >{tagNames[tid] || `#${tid}`}</Badge
                                    >
                                {/each}
                                {#if reg.node_tag_ids.length === 0}
                                    <span class="text-muted">None</span>
                                {/if}
                            </div>
                        </CardBody>
                        <div class="card-footer d-flex justify-content-end gap-2">
                            <Button
                                color="info"
                                size="sm"
                                onclick={() => openEditModal(reg)}
                            >
                                Edit
                            </Button>
                            <Button
                                color="danger"
                                size="sm"
                                onclick={() => handleDelete(reg.tag_id)}
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

<Modal {isModalOpen} toggle={closeModal}>
    <ModalHeader>
        {editReg ? "Edit Node Registration" : "Register Node"}
    </ModalHeader>
    <ModalBody>
        <FormGroup>
            <Label>Client</Label>
            <Input
                type="select"
                bind:value={newClientId}
                onchange={(e) => {
                    newClientId = Number(e.currentTarget.value);
                }}
            >
                {#each clients as client}
                    <option value={client.id}>{client.name}</option>
                {/each}
            </Input>
        </FormGroup>
        <FormGroup>
            <Label>Category</Label>
            <Input
                type="select"
                onchange={async (e) => {
                    const catId = Number(e.currentTarget.value);
                    if (catId) await fetchTagsForCategory(catId);
                }}
            >
                <option value="">Select category to filter tags</option>
                {#each allCategories as cat}
                    <option value={cat.id}>{cat.name}</option>
                {/each}
            </Input>
        </FormGroup>
        <FormGroup>
            <Label>Tag</Label>
            <Input
                type="select"
                bind:value={selectedTagId}
                onchange={(e) => {
                    selectedTagId = Number(e.currentTarget.value) || null;
                }}
            >
                <option value="">Select tag</option>
                {#each availableTags as tag}
                    <option value={tag.id}>{tag.name}</option>
                {/each}
            </Input>
        </FormGroup>
        <FormGroup>
            <Label>Node UUID</Label>
            <Input
                type="text"
                placeholder="00000000-0000-0000-0000-000000000000"
                bind:value={newNodeId}
            />
        </FormGroup>
        <FormGroup>
            <Label>Description (optional)</Label>
            <Input type="text" bind:value={newDescription} />
        </FormGroup>
        <FormGroup>
            <Label>Link (optional)</Label>
            <Input type="text" bind:value={newLink} />
        </FormGroup>
        <FormGroup>
            <Label>Attached Tag IDs (comma-separated)</Label>
            <Input
                type="text"
                placeholder="1, 2, 3"
                bind:value={newNodeTagIds}
            />
        </FormGroup>
    </ModalBody>
    <ModalFooter>
        <Button
            color="primary"
            disabled={!selectedTagId || !newClientId || !newNodeId}
            onclick={handleSubmit}
        >
            {editReg ? "Update" : "Register"}
        </Button>
        <Button color="secondary" onclick={closeModal}>Cancel</Button>
    </ModalFooter>
</Modal>
