--- Create Clients & Categories

CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

--- Create Tags

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category INTEGER NOT NULL,
    is_exposed BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (category) REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tag_relations (
    tag_id INTEGER NOT NULL,
    dependent_tag_id INTEGER NOT NULL
);

--- Create Registered Nodes

CREATE TABLE IF NOT EXISTS registered_nodes (
    tag_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    client_node_id INTEGER NOT NULL,
    params JSONB NOT NULL DEFAULT '{}',
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);