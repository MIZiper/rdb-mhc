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
        Row,
        Spinner,
    } from "@sveltestrap/sveltestrap";
    import type { Client, Category } from "../schema";
    import { onMount } from "svelte";

    let clients: Client[] = $state([]);
    let categories: Category[] = $state([]);
    let tagCount: Record<number, number> = $state({});
    let nodeCount: number = $state(0);
    let loading: boolean = $state(true);

    async function fetchData() {
        loading = true;
        const [clientsRes, catsRes, nodesRes] = await Promise.all([
            fetch("/api/clients"),
            fetch("/api/clients/all/categories"),
            fetch("/api/nodes/"),
        ]);

        if (clientsRes.ok) clients = await clientsRes.json();
        if (catsRes.ok) categories = await catsRes.json();
        if (nodesRes.ok) {
            const nodesData = await nodesRes.json();
            nodeCount = nodesData.total;
        }

        const counts: Record<number, number> = {};
        for (const cat of categories) {
            const res = await fetch(
                `/api/tags?category_id=${cat.id}`,
            );
            if (res.ok) {
                const tags = await res.json();
                counts[cat.id!] = tags.length;
            }
        }
        tagCount = counts;
        loading = false;
    }

    function getClientCategoryCount(clientId: number | null): number {
        return categories.filter((c) => c.client_id === clientId).length;
    }

    function getClientTagCount(clientId: number | null): number {
        return categories
            .filter((c) => c.client_id === clientId)
            .reduce((sum, c) => sum + (tagCount[c.id!] || 0), 0);
    }

    onMount(fetchData);
</script>

<Container fluid class="mt-3">
    <Row class="mb-3">
        <Col>
            <h3>MetaHub Dashboard</h3>
            <p class="text-muted">
                Tag management, registration and search platform
            </p>
        </Col>
    </Row>

    {#if loading}
        <div class="text-center py-5">
            <Spinner />
        </div>
    {:else}
        <Row class="mb-4">
            <Col md="3">
                <Card class="text-center">
                    <CardBody>
                        <h2>{clients.length}</h2>
                        <p class="text-muted">Clients</p>
                    </CardBody>
                </Card>
            </Col>
            <Col md="3">
                <Card class="text-center">
                    <CardBody>
                        <h2>{categories.length}</h2>
                        <p class="text-muted">Categories</p>
                    </CardBody>
                </Card>
            </Col>
            <Col md="3">
                <Card class="text-center">
                    <CardBody>
                        <h2>
                            {Object.values(tagCount).reduce(
                                (sum, n) => sum + n,
                                0,
                            )}
                        </h2>
                        <p class="text-muted">Tags</p>
                    </CardBody>
                </Card>
            </Col>
            <Col md="3">
                <Card class="text-center">
                    <CardBody>
                        <h2>{nodeCount}</h2>
                        <p class="text-muted">Registered Nodes</p>
                    </CardBody>
                </Card>
            </Col>
        </Row>

        <h5>Clients</h5>
        {#if clients.length === 0}
            <p class="text-muted">
                No clients registered yet.
                <Button
                    color="link"
                    href="/clients"
                >Register a client</Button>
            </p>
        {:else}
            <Row>
                {#each clients as client}
                    <Col md="6" lg="4" class="mb-3">
                        <Card>
                            <CardHeader>
                                <CardTitle>{client.name}</CardTitle>
                            </CardHeader>
                            <CardBody>
                                <div class="mb-1">
                                    <strong>Categories:
                                    </strong>{getClientCategoryCount(client.id)}
                                </div>
                                <div class="mb-1">
                                    <strong>Tags:
                                    </strong>{getClientTagCount(client.id)}
                                </div>
                                {#if client.host}
                                    <div class="mb-1">
                                        <strong>TC Host:
                                        </strong>{client.host}
                                    </div>
                                {:else}
                                    <div class="mb-1 text-muted">
                                        No downstream host
                                    </div>
                                {/if}
                            </CardBody>
                            <div class="card-footer">
                                <Button
                                    color="primary"
                                    size="sm"
                                    href={`/admin/${client.id}`}
                                >
                                    Manage Tags
                                </Button>
                            </div>
                        </Card>
                    </Col>
                {/each}
            </Row>
        {/if}
    {/if}
</Container>
