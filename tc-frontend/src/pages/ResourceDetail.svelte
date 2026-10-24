<script lang="ts">
    import {
        Badge,
        Button,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        Col,
        Container,
        Input,
        Label,
        Row,
    } from "@sveltestrap/sveltestrap";

    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import type { ItemDetail } from "../types";
    import { getContext, onMount } from "svelte";
    import { constructTagsById, fetchTagsInfo } from "../lib/api/metahub";
    import { registry, type BaseProcessor } from "../modules/registry";
    import { authFetch, hasRole, getAuthContext } from "../lib/auth";
    import { deleteImage } from "../lib/api/files";
    import {
        statusColor,
        statusLabel,
        typeColor,
        visibilityColor,
    } from "../lib/utils/ui";
    import TagChip from "../components/ui/TagChip.svelte";

    let router: any = getContext("router");
    let params = router.route.getParams("/items/:id");
    let item_id = params.id;
    let item: ItemDetail | null = $state(null);
    let metahub_host = (getContext("mh_host") as string) || "";
    let processor: BaseProcessor | null = $state(null);
    let loadError = $state("");

    let editMode = $state(false);
    let editTitle = $state("");
    let editDescription = $state("");
    let editVisibility = $state("public");
    let editVisibilityPreset = $state("public");
    let editCustomVisibility = $state("");
    let editTags: TagMeta[] = $state([]);
    let tagSelectorOpen = $state(false);
    let saving = $state(false);
    let saveError = $state("");

    let contentEditMode = $state(false);
    let contentEditor: any = $state(null);
    let contentSaving = $state(false);
    let contentError = $state("");

    const STATUS_OPTIONS = ["draft", "pending_review", "published", "archived"];
    let selectedStatus = $state("draft");
    let statusSaving = $state(false);
    let statusError = $state("");

    function checkCanEdit(): boolean {
        if (hasRole("nodes:edit_any")) return true;
        if (!item) return false;
        return item.creator_sub === getAuthContext()?.user?.sub;
    }

    onMount(async () => {
        const res = await authFetch(`/api/nodes/${item_id}/data`);
        if (!res.ok) {
            loadError = res.status === 404 ? "Resource not found" : "Failed to load resource";
            return;
        }
        const data = await res.json();

        const tags_cache = await fetchTagsInfo(metahub_host, data.tag_ids);

        item = {
            id: data.id,
            title: data.title,
            description: data.description,
            update_time: new Date(data.updated_at),
            tags: constructTagsById(data.tag_ids, tags_cache),
            data_type: data.data_type,
            content: data.content,
            creator_name: data.creator_name,
            creator_sub: data.creator_sub,
            status: data.status,
            visibility: data.visibility || "public",
            source_system: data.source_system ?? null,
            source_id: data.source_id ?? null,
            source_part: data.source_part ?? null,
            source_url: data.source_url ?? null,
        };
        selectedStatus = data.status;

        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get("edit") === "1" && checkCanEdit()) {
            enterEdit();
        }

        processor = registry.getProcessor(item.data_type || "");
    });

    function enterEdit() {
        if (!item) return;
        editMode = true;
        editTitle = item.title;
        editDescription = item.description;
        editVisibility = item.visibility;
        editVisibilityPreset = ["public", "internal", "confidential"].includes(item.visibility)
            ? item.visibility
            : "__custom__";
        editCustomVisibility = editVisibilityPreset === "__custom__" ? item.visibility : "";
        editTags = [...item.tags];
        saveError = "";
    }

    function cancelEdit() {
        editMode = false;
        saveError = "";
    }

    function enterContentEdit() {
        contentEditMode = true;
        contentError = "";
    }

    function cancelContentEdit() {
        contentEditMode = false;
        contentError = "";
    }

    async function saveContent() {
        if (!item || !contentEditor) return;
        contentSaving = true;
        contentError = "";
        try {
            const content = contentEditor.getContent();
            const res = await authFetch(`/api/nodes/${item_id}/data`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(content),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                contentError = err.detail || "Failed to save content";
                return;
            }
            const data = await res.json();
            const removed =
                typeof contentEditor.getRemovedFileIds === "function"
                    ? contentEditor.getRemovedFileIds()
                    : [];
            for (const fileId of removed) {
                deleteImage(fileId);
            }
            item = { ...item, content: data.content, update_time: new Date(data.updated_at) };
            contentEditMode = false;
        } catch (e: any) {
            contentError = e.message;
        } finally {
            contentSaving = false;
        }
    }

    async function saveStatus() {
        if (!item) return;
        statusSaving = true;
        statusError = "";
        try {
            const res = await authFetch(`/api/nodes/${item_id}/state`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: selectedStatus }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                statusError = err.detail || "Failed to update status";
                return;
            }
            const data = await res.json();
            item = { ...item, status: data.status, update_time: new Date(data.updated_at) };
        } catch (e: any) {
            statusError = e.message;
        } finally {
            statusSaving = false;
        }
    }

    function useTags(_tags: TagMeta[]) {
        editTags = _tags;
        tagSelectorOpen = false;
    }

    async function saveMeta() {
        if (!item) return;
        saving = true;
        saveError = "";
        try {
            const resolvedVisibility = editVisibilityPreset === "__custom__" ? editCustomVisibility : editVisibilityPreset;
            const res = await authFetch(`/api/nodes/${item_id}/meta`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: editTitle,
                    description: editDescription,
                    visibility: resolvedVisibility,
                    tag_ids: editTags.map((t) => t.id),
                }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                saveError = err.detail || "Failed to save";
                return;
            }
            const data = await res.json();
            const tags_cache = await fetchTagsInfo(metahub_host, data.tag_ids);
            item = {
                ...item,
                title: data.title,
                description: data.description,
                update_time: new Date(data.updated_at),
                tags: constructTagsById(data.tag_ids, tags_cache),
                visibility: data.visibility || "public",
            };
            editMode = false;
        } catch (e: any) {
            saveError = e.message;
        } finally {
            saving = false;
        }
    }
</script>

<Container class="my-3" fluid>
    {#if item}
        <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3">
            <div class="flex-grow-1">
                <div class="d-flex flex-wrap align-items-center gap-2 mb-1">
                    {#if item.data_type}
                        <a
                            class="badge rounded-pill text-white text-decoration-none"
                            style="background:{typeColor(item.data_type)}"
                            href="/types/{encodeURI(item.data_type)}"
                        >{item.data_type}</a>
                    {/if}
                    <Badge class="text-bg-{statusColor(item.status)}">
                        {statusLabel(item.status)}
                    </Badge>
                    {#if item.visibility !== "public"}
                        <Badge class="text-bg-{visibilityColor(item.visibility)}">
                            {item.visibility}
                        </Badge>
                    {/if}
                </div>
                <h2 class="h3 mb-1">{item.title}</h2>
                {#if item.description}
                    <p class="text-secondary mb-2">{item.description}</p>
                {/if}
                <div class="d-flex flex-wrap align-items-center gap-1">
                    <span class="small text-secondary me-1">Tags</span>
                    {#each item.tags as tag}
                        <TagChip {tag} metahubHost={metahub_host} />
                    {:else}
                        <span class="small text-muted">No tags</span>
                    {/each}
                </div>
            </div>
            {#if checkCanEdit() && !editMode}
                <Button color="outline-secondary" size="sm" onclick={enterEdit}>
                    Edit details
                </Button>
            {/if}
        </div>

        <Row class="g-4">
            <Col lg="8">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="mb-0">Content</h5>
                    {#if checkCanEdit() && processor?.editor && !contentEditMode}
                        <Button color="link" size="sm" class="px-0" onclick={enterContentEdit}>
                            Edit Content
                        </Button>
                    {/if}
                </div>

                {#if !processor}
                    <p>Registered type: [{item.data_type}] (no viewer found)</p>
                    <pre>{JSON.stringify(item.content, null, 2)}</pre>
                {:else if contentEditMode}
                    <div class="content-edit">
                        <processor.editor bind:this={contentEditor} initial={item.content} />
                        {#if contentError}
                            <div class="text-danger mt-2">{contentError}</div>
                        {/if}
                        <div class="mt-2">
                            <Button color="primary" disabled={contentSaving} onclick={saveContent}>
                                {contentSaving ? "Saving..." : "Save Content"}
                            </Button>
                            <Button color="secondary" class="ms-2" onclick={cancelContentEdit}>Cancel</Button>
                        </div>
                    </div>
                {:else}
                    <processor.viewer content_in={item.content} />
                {/if}
            </Col>

            <Col lg="4">
                {#if editMode}
                    <Card class="shadow-sm">
                        <CardHeader class="fw-semibold">Edit details</CardHeader>
                        <CardBody>
                            <Label>Title</Label>
                            <Input type="text" bind:value={editTitle} />
                            <Label class="mt-2">Description</Label>
                            <Input type="textarea" bind:value={editDescription} />

                            <Label class="mt-2">Visibility</Label>
                            <Input type="select" bind:value={editVisibilityPreset}>
                                <option value="public">Public</option>
                                <option value="internal">Internal</option>
                                <option value="confidential">Confidential</option>
                                <option value="__custom__">Custom...</option>
                            </Input>
                            {#if editVisibilityPreset === "__custom__"}
                                <Input
                                    type="text"
                                    class="mt-2"
                                    placeholder="e.g. proj_a"
                                    bind:value={editCustomVisibility}
                                />
                            {/if}

                            <Label class="mt-3">Tags</Label>
                            <div class="d-flex flex-wrap align-items-center gap-1">
                                {#each editTags as tag}
                                    <TagChip {tag} link={false} />
                                {:else}
                                    <span class="small text-muted">No tags</span>
                                {/each}
                                <Button
                                    size="sm"
                                    color="outline-secondary"
                                    class="ms-1"
                                    onclick={() => { tagSelectorOpen = true; }}
                                >
                                    Edit Tags
                                </Button>
                            </div>
                        </CardBody>
                        <CardFooter>
                            {#if saveError}
                                <div class="text-danger small mb-2">{saveError}</div>
                            {/if}
                            <Button color="primary" disabled={saving} onclick={saveMeta}>
                                {saving ? "Saving..." : "Save"}
                            </Button>
                            <Button color="secondary" class="ms-2" onclick={cancelEdit}>Cancel</Button>
                        </CardFooter>
                    </Card>
                {:else}
                    <Card class="shadow-sm">
                        <CardHeader class="fw-semibold">Details</CardHeader>
                        <CardBody>
                            <dl class="row small mb-0">
                                <dt class="col-4 fw-normal text-secondary">Creator</dt>
                                <dd class="col-8 mb-2 text-truncate">{item.creator_name || "—"}</dd>
                                <dt class="col-4 fw-normal text-secondary">Updated</dt>
                                <dd class="col-8 mb-2">{item.update_time.toLocaleDateString()}</dd>
                                <dt class="col-4 fw-normal text-secondary">Type</dt>
                                <dd class="col-8 mb-2">{item.data_type || "—"}</dd>
                                <dt class="col-4 fw-normal text-secondary">Visibility</dt>
                                <dd class="col-8 mb-2">{item.visibility}</dd>
                                {#if item.source_url}
                                    <dt class="col-4 fw-normal text-secondary">Source</dt>
                                    <dd class="col-8 mb-0">
                                        <a href={item.source_url} target="_blank" rel="noreferrer">
                                            {item.source_system || "external"}{item.source_part ? ` / ${item.source_part}` : ""}
                                        </a>
                                    </dd>
                                {/if}
                            </dl>
                            {#if hasRole("nodes:review")}
                                <Label class="mt-3">Status</Label>
                                <Input type="select" bind:value={selectedStatus}>
                                    {#each STATUS_OPTIONS as option}
                                        <option value={option}>{option}</option>
                                    {/each}
                                </Input>
                                {#if statusError}
                                    <div class="text-danger small mt-1">{statusError}</div>
                                {/if}
                                <Button
                                    color="outline-secondary"
                                    size="sm"
                                    class="mt-2"
                                    disabled={statusSaving}
                                    onclick={saveStatus}
                                >
                                    {statusSaving ? "Saving..." : "Update status"}
                                </Button>
                            {/if}
                        </CardBody>
                    </Card>
                {/if}
            </Col>
        </Row>
    {:else if loadError}
        <p class="text-danger">{loadError}</p>
    {:else}
        <p class="text-muted">Loading...</p>
    {/if}
</Container>

<TagsSelector
    isOpen={tagSelectorOpen}
    onSelect={useTags}
    onCancel={() => { tagSelectorOpen = false; }}
/>
