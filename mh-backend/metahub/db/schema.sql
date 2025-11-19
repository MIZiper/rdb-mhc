--- Create Clients & Categories

CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    client_id INTEGER NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

--- Create Tags

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL,
    is_exposed BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tag_relations (
    tag_id INTEGER NOT NULL,
    dependent_tag_id INTEGER NOT NULL,
    relation_type VARCHAR NOT NULL CHECK (relation_type IN ('PRIMARY', 'DEPENDENCY')),
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    FOREIGN KEY (dependent_tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (tag_id, dependent_tag_id)
);

ALTER TABLE tag_relations ADD CONSTRAINT no_self_relation CHECK (tag_id <> dependent_tag_id);
ALTER TABLE tag_relations ADD CONSTRAINT primary_unique UNIQUE (tag_id) WHERE relation_type = 'PRIMARY';

--- Create Registered Nodes

CREATE TABLE IF NOT EXISTS registered_nodes (
    tag_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    client_node_id INTEGER NOT NULL,
    params JSONB NOT NULL DEFAULT '{}',
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);