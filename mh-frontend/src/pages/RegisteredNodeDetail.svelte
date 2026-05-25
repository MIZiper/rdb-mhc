<script lang="ts">
    import {
        Badge,
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
    import type { NodeRegistration, Client } from "../schema";
    import { getContext, onMount } from "svelte";

    const router = getContext<{ route: { getParams: (path: string) => void; params: Record<string, string> } }>("router");
    router.route.getParams("/registered/:tag_id/:tag_str");

    let tagId = Number(router.route.params.tag_id);
    let tagName: string = $state(decodeURI(router.route.params.tag_str));

    let registration: NodeRegistration | null = $state(null);
    let notFound = $state(false);
    let loading = $state(true);
    let clients: Client[] = $state([]);
    let tagNames: Record<number, string> = $state({});

    onMount(() => {
        fetchRegistration();
        fetchClients();
    });

    async function fetchRegistration() {
        loading = true;
        const res = await fetch(`/api/nodes/by-tag/${tagId}`);
        if (res.status === 404) {
            notFound = true;
            loading = false;
            return;
        }
        if (res.ok) {
            const reg = await res.json() as NodeRegistration;
            registration = reg;
            await fetchTagNames(reg);
        }
        loading = false;
    }

    async function fetchTagNames(reg: NodeRegistration) {
        const allTagIds = new Set<number>();
        allTagIds.add(reg.tag_id);
        for (const tid of reg.node_tag_ids) {
            allTagIds.add(tid);
        }
        const res = await fetch("/api/tags/resolve", {
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
            tagName = tagNames[reg.tag_id] || tagName;
        }
    }

    async function fetchClients() {
        const res = await fetch("/api/clients");
        if (res.ok) {
            clients = await res.json();
        }
    }
</script>

<Container fluid class="mt-2">
    <Row>
        <Col>
            <a href="/nodes" class="text-decoration-none">&larr; Back to Registered Nodes</a>
        </Col>
    </Row>

    {#if loading}
        <div class="text-center py-5">
            <Spinner />
        </div>
    {:else if notFound || !registration}
        <Row class="mt-4">
            <Col md="8">
                <Card>
                    <CardHeader>
                        <CardTitle>Tag: {tagName}</CardTitle>
                    </CardHeader>
                    <CardBody>
                        <p class="text-muted">
                            No node is registered for this tag yet.
                        </p>
                        <p>
                            <a href="/nodes" class="btn btn-primary">
                                Register a Node
                            </a>
                        </p>
                    </CardBody>
                </Card>
            </Col>
        </Row>
    {:else}
        {@const reg = registration!}
        {@const client = clients.find((c) => c.id === reg.client_id)}
        <Row class="mt-4">
            <Col md="8">
                <Card>
                    <CardHeader>
                        <CardTitle>Tag: {tagName}</CardTitle>
                        <CardSubtitle>
                            {client?.name || `Client #${reg.client_id}`}
                        </CardSubtitle>
                    </CardHeader>
                    <CardBody>
                        <table class="table table-sm table-borderless">
                            <tbody>
                                <tr>
                                    <td class="text-muted" style="width: 120px">Tag ID</td>
                                    <td>{reg.tag_id}</td>
                                </tr>
                                <tr>
                                    <td class="text-muted">Client</td>
                                    <td>
                                        {client?.name || `#${reg.client_id}`}
                                        {#if client?.host}
                                            <span class="ms-2 text-muted">({client.host})</span>
                                        {/if}
                                    </td>
                                </tr>
                                <tr>
                                    <td class="text-muted">Node UUID</td>
                                    <td>
                                        <code>{reg.client_node_id}</code>
                                    </td>
                                </tr>
                                {#if reg.params?.description}
                                    <tr>
                                        <td class="text-muted">Description</td>
                                        <td>{String(reg.params.description)}</td>
                                    </tr>
                                {/if}
                                {#if reg.params?.link}
                                    <tr>
                                        <td class="text-muted">Link</td>
                                        <td>
                                            <a
                                                href={String(reg.params.link)}
                                                target="_blank"
                                            >
                                                {reg.params.link}
                                            </a>
                                        </td>
                                    </tr>
                                {/if}
                            </tbody>
                        </table>

                        <div class="mt-3">
                            <strong>Bound Tags: </strong>
                            {#each reg.node_tag_ids as tid}
                                <Badge class="me-1">
                                    {tagNames[tid] || `#${tid}`}
                                </Badge>
                            {/each}
                            {#if reg.node_tag_ids.length === 0}
                                <span class="text-muted">None</span>
                            {/if}
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Row>
    {/if}
</Container>
