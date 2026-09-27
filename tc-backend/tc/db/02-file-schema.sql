-- Stored files (images and other uploaded assets)
-- Bytes live on disk under TC_STORAGE_ROOT; this table holds metadata.

CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    original_name VARCHAR(255),
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    width INTEGER,
    height INTEGER,
    stored_path VARCHAR(512) NOT NULL,
    thumb_path VARCHAR(512),
    creator_sub VARCHAR(255),
    creator_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_files_node_id ON files(node_id);
CREATE INDEX IF NOT EXISTS idx_files_creator_sub ON files(creator_sub);
