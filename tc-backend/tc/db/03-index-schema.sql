-- Derived projection index for cross-type retrieval / aggregation.
--
-- The source of truth stays in nodes.content (JSONB); these tables are a
-- type-aware inverted index. They are maintained on every content write by
-- tc.services.node_content using the type descriptors in tc.types.

-- Seeded from code (tc.types.registry) on startup.
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
CREATE INDEX IF NOT EXISTS idx_data_types_enabled ON data_types(enabled);
