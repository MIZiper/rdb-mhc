<script lang="ts">
    import {
        Button,
        Col,
        Container,
        Icon,
        Input,
        ListGroup,
        Row,
        Tooltip,
    } from "@sveltestrap/sveltestrap";
    import { getContext } from "svelte";
    import { searchParams } from "sv-router";
    import ResourceItem from "../components/ResourceItem.svelte";
    import Pagination from "../components/Pagination.svelte";
    import { authFetch, getAuthContext } from "../lib/auth";
    import { useNodeList } from "../lib/useNodeList.svelte";

    let router: any = getContext("router");
    const metahubHost = (getContext("mh_host") as string) || "";
    const list = useNodeList(metahubHost, 10);

    let searchBind = $state("");
    let qSearch = $state("");

    function preprocessTsQuery(input: string): string {
        const trimmed = input.trim();
        if (!trimmed) return "";
        // Already contains tsquery operators: keep as-is.
        if (/[&|!<->]/.test(trimmed)) return trimmed;
        return trimmed.split(/\s+/).filter(Boolean).join(" & ");
    }

    function loadPage(q: string, page: number) {
        const qs = new URLSearchParams({
            page: String(page),
            q,
            page_size: "10",
        }).toString();
        qSearch = q;
        searchBind = q;
        list.load(() => authFetch(`/api/nodes/?${qs}`).then((r) => r.json()), page);
    }

    function navigate(q: string, page: number) {
        router.navigate("/", { search: { q, page } });
    }

    $effect(() => {
        const q = String(searchParams.get("q") || "");
        const page = parseInt(String(searchParams.get("page") || "1"), 10);
        const _auth = getAuthContext();
        loadPage(q, isNaN(page) || page < 1 ? 1 : page);
    });
</script>

<Container class="my-3" fluid>
    <h4 class="mb-3">Resources</h4>

    <Row class="mb-3">
        <Col>
            <Input
                type="search"
                placeholder="Search by text"
                bind:value={searchBind}
                onkeypress={(e) => {
                    if (e.key === "Enter")
                        navigate(preprocessTsQuery(searchBind), 1);
                }}
            />
        </Col>
        <Col xs="auto">
            <Tooltip target="tsquery-info">
                Use 'abc', 'abc &amp; def', 'abc | def', 'abc &amp; !def', 'abc:*' ...
                for the query.
            </Tooltip>
            <Icon name="info" id="tsquery-info" />
            <Button onclick={() => navigate(preprocessTsQuery(searchBind), 1)}>
                Search
            </Button>
        </Col>
    </Row>

    {#if list.loading}
        <p class="text-muted">Loading...</p>
    {:else if list.error}
        <p class="text-danger">Error: {list.error}</p>
    {:else if list.items.length === 0}
        <p class="text-muted">No results found.</p>
    {:else}
        <p class="text-muted small">
            {list.total} results (Page {list.page} / {list.totalPages})
        </p>

        <ListGroup class="mt-2 d-flex flex-column gap-2">
            {#each list.items as item}
                <ResourceItem {item} />
            {/each}
        </ListGroup>

        <Pagination
            page={list.page}
            totalPages={list.totalPages}
            onchange={(p) => navigate(qSearch, p)}
        />
    {/if}
</Container>
