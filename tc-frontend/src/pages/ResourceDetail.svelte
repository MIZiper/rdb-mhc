<script lang="ts">
    import {
        Badge,
        Button,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardSubtitle,
        CardTitle,
        Col,
        Container,
        Input,
        Label,
        Row,
    } from "@sveltestrap/sveltestrap";

    import { TagsSelector, type TagMeta } from "@mizip/metahub";
    import type { ItemDetail } from "../schema";
    import { getContext, onMount } from "svelte";
    import { construct_tags_by_ids, fetch_tags_info } from "./FetchMetaHubTags";
    import { registry, type BaseProcessor } from "../lib/processor";
    import { authFetch, hasRole, getAuthContext } from "../lib/auth";

    let router: any = getContext("router");
    let params = router.route.getParams("/items/:id");
    let item_id = params.id;
    let item: ItemDetail | null = $state(null);
    let metahub_host = (getContext("mh_host") as string) || "";
    let processor: BaseProcessor | null = $state(null);

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

    function checkCanEdit(): boolean {
        if (hasRole("nodes:edit_any")) return true;
        if (!item) return false;
        return item.creator_sub === getAuthContext()?.user?.sub;
    }

    onMount(async () => {
        const res = await fetch(`/api/nodes/${item_id}/data`);
        const data = await res.json();

        const tags_cache = await fetch_tags_info(metahub_host, data.tag_ids);

        item = {
            id: data.id,
            title: data.title,
            description: data.description,
            update_time: new Date(data.updated_at),
            tags: construct_tags_by_ids(data.tag_ids, tags_cache),
            data_type: data.data_type,
            content: data.content,
            creator_name: data.creator_name,
            creator_sub: data.creator_sub,
            status: data.status,
            visibility: data.visibility || "public",
        };

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
            const tags_cache = await fetch_tags_info(metahub_host, data.tag_ids);
            item = {
                ...item,
                title: data.title,
                description: data.description,
                update_time: new Date(data.updated_at),
                tags: construct_tags_by_ids(data.tag_ids, tags_cache),
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

<Container class="my-2" fluid>
    <Row>
        <Col>
            {#if item}
                {#if !processor}
                    <p>Registered type: [{item.data_type}] (no viewer found)</p>
                    <pre>{JSON.stringify(item.content, null, 2)}</pre>
                {:else}
                    <processor.viewer content_in={item.content} />
                {/if}
            {:else}
                <p>Loading...</p>
            {/if}
        </Col>
        <Col xs="4">
            {#if item}
                <Card>
                    <CardHeader></CardHeader>
                    <CardBody>
                        {#if editMode}
                            <Label>Title</Label>
                            <Input type="text" bind:value={editTitle} />
                            <Label class="mt-2">Description</Label>
                            <Input type="textarea" bind:value={editDescription} />

                            <Label class="mt-2">Visibility</Label>
                            <select class="form-select" bind:value={editVisibilityPreset}>
                                <option value="public">Public</option>
                                <option value="internal">Internal</option>
                                <option value="confidential">Confidential</option>
                                <option value="__custom__">Custom...</option>
                            </select>
                            {#if editVisibilityPreset === "__custom__"}
                                <Input
                                    type="text"
                                    class="mt-2"
                                    placeholder="e.g. proj_a"
                                    bind:value={editCustomVisibility}
                                />
                            {/if}

                            <div class="mt-2">
                                <i>Tags:</i>
                                <span>{editTags.map((e) => e.name).join(", ")}</span>
                                <Button size="sm" class="ms-2" onclick={() => { tagSelectorOpen = true; }}>
                                    Edit Tags
                                </Button>
                            </div>
                        {:else}
                            <CardSubtitle>{item.title}</CardSubtitle>
                            {item.description}
                            {#if item.visibility !== "public"}
                                <Badge color="info" class="mt-2 d-block" style="width:fit-content">
                                    {item.visibility}
                                </Badge>
                            {/if}
                        {/if}
                    </CardBody>
                    <CardFooter>
                        {#if editMode}
                            {#if saveError}
                                <div class="text-danger mb-2">{saveError}</div>
                            {/if}
                            <Button color="primary" disabled={saving} onclick={saveMeta}>
                                {saving ? "Saving..." : "Save"}
                            </Button>
                            <Button color="secondary" class="ms-2" onclick={cancelEdit}>Cancel</Button>
                        {:else}
                            {#each item.tags as tag}
                                <Badge
                                    pill
                                    class="me-1"
                                    href="/tags/{tag.id}/{encodeURI(tag.name)}"
                                >
                                    {tag.name}
                                </Badge>
                            {/each}
                            {#if checkCanEdit()}
                                <Button color="link" size="sm" class="ms-2" onclick={enterEdit}>Edit</Button>
                            {/if}
                        {/if}
                    </CardFooter>
                </Card>
            {:else}
                <p>Loading</p>
            {/if}
        </Col>
    </Row>
</Container>

<TagsSelector
    isOpen={tagSelectorOpen}
    onSelect={useTags}
    onCancel={() => { tagSelectorOpen = false; }}
/>
