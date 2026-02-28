<script lang="ts">
    // the search bar is integrated with tag search functionality

    import { Button, Col, Input, Row } from "@sveltestrap/sveltestrap";
</script>

<Row>
    <Col>
        <Input type="search" placeholder="Tags or content" />
    </Col>
    <Col xs="auto">
        <Button>Search</Button>
    </Col>
</Row>
