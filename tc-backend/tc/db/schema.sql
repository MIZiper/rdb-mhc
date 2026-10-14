-- TemplateClient database schema.
--
-- This single, idempotent file is the source of truth and is applied on
-- startup by tc.db.schema.ensure_schema. It merges what used to be
-- 00-base / 01-rdb / 02-file / 03-index.

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- Nodes (content records) and their tags
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nodes (
    id             UUID PRIMARY KEY DEFAULT uuidv7(),
    title          VARCHAR(100) NOT NULL,
    description    TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    creator_sub    VARCHAR(255),
    creator_name   VARCHAR(255),
    status         VARCHAR(50) NOT NULL DEFAULT 'draft',
    visibility     VARCHAR NOT NULL DEFAULT 'public',
    content        JSONB NOT NULL DEFAULT '{}',
    content_type   VARCHAR(50),
    valid          BOOLEAN NOT NULL DEFAULT TRUE,
    -- release / analysis links and freezing
    backlink       VARCHAR(255),
    frozenlink     VARCHAR(255),
    frozen         BOOLEAN NOT NULL DEFAULT FALSE,
    validate_key   VARCHAR(20) DEFAULT NULL,
    -- full-text search over title + description
    search_vector  TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))
    ) STORED
);
-- status values: draft, pending_review, published, archived

CREATE INDEX IF NOT EXISTS idx_nodes_search_vector ON nodes USING GIN (search_vector);

DROP TRIGGER IF EXISTS node_updated_at_trigger ON nodes;
CREATE TRIGGER node_updated_at_trigger
BEFORE UPDATE ON nodes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS node_tags (
    id       SERIAL PRIMARY KEY,
    node_id  UUID NOT NULL,
    tag_id   INTEGER NOT NULL,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_node_tags_tag_id ON node_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_node_tags_node_id ON node_tags(node_id);

-- ---------------------------------------------------------------------------
-- Files (bytes on disk under TC_STORAGE_ROOT; metadata here)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS files (
    id             UUID PRIMARY KEY DEFAULT uuidv7(),
    node_id        UUID REFERENCES nodes(id) ON DELETE CASCADE,
    data_type      VARCHAR(50) NOT NULL,
    original_name  VARCHAR(255),
    mime_type      VARCHAR(100) NOT NULL,
    size_bytes     BIGINT NOT NULL,
    width          INTEGER,
    height         INTEGER,
    stored_path    VARCHAR(512) NOT NULL,
    thumb_path     VARCHAR(512),
    creator_sub    VARCHAR(255),
    creator_name   VARCHAR(255),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_files_node_id ON files(node_id);
CREATE INDEX IF NOT EXISTS idx_files_creator_sub ON files(creator_sub);

-- ---------------------------------------------------------------------------
-- Cross-type retrieval / aggregation projection index.
--
-- The source of truth stays in nodes.content (JSONB); these tables are a
-- type-aware inverted index maintained on every content write.
-- ---------------------------------------------------------------------------

-- Seeded from code (tc.content_types.registry) on startup.
CREATE TABLE IF NOT EXISTS data_types (
    "type"        TEXT PRIMARY KEY,
    display_name  TEXT NOT NULL,
    version       INTEGER NOT NULL DEFAULT 0,
    "schema"      JSONB,
    fields        JSONB NOT NULL DEFAULT '[]'::jsonb,
    preview       JSONB NOT NULL DEFAULT '[]'::jsonb,
    ui            JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled       BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_data_types_enabled ON data_types(enabled);

-- Shared vocabulary: one row per canonical field key.
CREATE TABLE IF NOT EXISTS field_keys (
    key         TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    unit        TEXT,
    label       TEXT,
    comparable  BOOLEAN NOT NULL DEFAULT FALSE
);

-- One row per declared field value per node (list fields yield several rows).
CREATE TABLE IF NOT EXISTS node_fields (
    id          BIGSERIAL PRIMARY KEY,
    node_id     UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    key         TEXT NOT NULL,
    kind        TEXT NOT NULL,
    unit        TEXT,
    num_value   DOUBLE PRECISION,
    text_value  TEXT,
    ts_value    TIMESTAMPTZ,
    search_tsv  TSVECTOR
);

CREATE INDEX IF NOT EXISTS idx_node_fields_node_id ON node_fields(node_id);
CREATE INDEX IF NOT EXISTS idx_node_fields_key_num ON node_fields(key, num_value);
CREATE INDEX IF NOT EXISTS idx_node_fields_key_text ON node_fields(key, text_value);
CREATE INDEX IF NOT EXISTS idx_node_fields_key_ts ON node_fields(key, ts_value);
CREATE INDEX IF NOT EXISTS idx_node_fields_search_tsv ON node_fields USING GIN(search_tsv);
