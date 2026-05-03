--- Create Clients & Categories

CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    host VARCHAR(255)
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
    exposed BOOLEAN NOT NULL DEFAULT FALSE,
    parent_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES tags(id) ON DELETE SET NULL
);

--- Create Registered Nodes

CREATE TABLE IF NOT EXISTS registered_nodes (
    tag_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    client_node_id UUID NOT NULL,
    node_tag_ids INTEGER[],
    params JSONB NOT NULL DEFAULT '{}',
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE (tag_id)
);
