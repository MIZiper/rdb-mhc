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

    let tags: Tag[] = $state([]);
    function useTags(_tags: Tag[]) {
        tags = _tags;
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
                    <Input type="text" />
                    <Label>Description</Label>
                    <Input type="textarea" />
                    <Label>Analysis</Label>
                    <Input type="url" placeholder="https://..." />
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
                    <Button color="primary">Add Resource</Button>
                </CardFooter>
            </Card>
        </Col>
    </Row>
</Container>

<TagsSelector isOpen={true} onSelect={useTags} />
