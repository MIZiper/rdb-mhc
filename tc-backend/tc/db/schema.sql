CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    creator_signature VARCHAR(20),
    validate_key VARCHAR(20) DEFAULT NULL,
    frozen BOOLEAN NOT NULL DEFAULT FALSE,
    valid BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TRIGGER node_updated_at_trigger
BEFORE UPDATE ON nodes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS node_tags (
    id SERIAL PRIMARY KEY,
    node_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL, -- no restriction since defined in metahub
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);