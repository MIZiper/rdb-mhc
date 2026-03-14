-- The base node/tags database
-- Can be used by non-RDB but MetaHub applications

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS nodes (
    id UUID PRIMARY KEY DEFAULT uuidv7(), -- Require PostgreSQL 18+, for native uuid v7 support
    title VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    creator_signature VARCHAR(20), -- can be hash of creator_signature
    valid BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TRIGGER node_updated_at_trigger
BEFORE UPDATE ON nodes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS node_tags (
    id SERIAL PRIMARY KEY,
    node_id UUID NOT NULL,
    tag_id INTEGER NOT NULL, -- no restriction since defined in metahub
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Context search
ALTER TABLE nodes
ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))) STORED;

CREATE INDEX idx_nodes_search_vector ON nodes USING GIN (search_vector);

-- Index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_node_tags_tag_id ON node_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_node_tags_node_id ON node_tags(node_id);