<script lang="ts">
    import { TagsSelector, type Tag } from "@mizip/metahub";
    import {
        Button,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardTitle,
        Col,
        Container,
        Input,
        Label,
        Row,
    } from "@sveltestrap/sveltestrap";

    let title: string = $state("");
    let description: string = $state("");
    let analysis_link: string = $state("");
    let tags: Tag[] = $state([]);
    function useTags(_tags: Tag[]) {
        tags = _tags;
    }

    async function addResource() {
        const res = await fetch(`/api/nodes/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title,
                description,
                backlink: analysis_link,
                tags: tags.map((e) => ({ id: e.id, name: e.name })),
            }),
        });
        if (!res.ok) {
        }
    }
</script>

<Container fluid>
    <Row class="mt-2">
        <Col>
            <select>
                <option value="abc">ABC</option>
            </select>
        </Col>
        <Col>
            <Card>
                <CardHeader>
                    <CardTitle>New Resource</CardTitle>
                </CardHeader>
                <CardBody>
                    <Label>Title</Label>
                    <Input type="text" bind:value={title} />
                    <Label>Description</Label>
                    <Input type="textarea" bind:value={description} />
                    <Label>Analysis</Label>
                    <Input
                        type="url"
                        placeholder="https://..."
                        bind:value={analysis_link}
                    />
                    <Label>Tags</Label>
                    <p>
                        <i>Tags:</i>
                        <span>{tags.map((e) => e.name).join(", ")}</span>
                        <br />
                        <i>TagsStr:</i>
                        <span>{tags.map((e) => e.id).join(";")}</span>
                    </p>
                </CardBody>
                <CardFooter>
                    <Button color="primary" onclick={addResource}
                        >Add Resource</Button
                    >
                </CardFooter>
            </Card>
        </Col>
    </Row>
</Container>

<TagsSelector isOpen={true} onSelect={useTags} />
