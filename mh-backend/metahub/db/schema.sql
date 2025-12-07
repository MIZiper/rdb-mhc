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
CREATE UNIQUE INDEX primary_unique_idx ON tag_relations (tag_id) WHERE (relation_type = 'PRIMARY');

CREATE OR REPLACE FUNCTION set_tag_primary(
    p_tag_id int,
    p_new_primary int DEFAULT NULL
) RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_new_primary IS NULL THEN
        -- 清空 PRIMARY（不影响 DEPENDENCY）
        DELETE FROM tag_relations
        WHERE tag_id = p_tag_id
          AND relation_type = 'PRIMARY';
        RETURN;
    END IF;

    -- 1) 将指定 dependent 设为 PRIMARY（不存在则插入，存在则更新类型）
    INSERT INTO tag_relations (tag_id, dependent_tag_id, relation_type)
    VALUES (p_tag_id, p_new_primary, 'PRIMARY')
    ON CONFLICT (tag_id, dependent_tag_id)
    DO UPDATE SET relation_type = 'PRIMARY';

    -- 2) 删除该 tag_id 的其他 PRIMARY，保证唯一
    DELETE FROM tag_relations tr
    WHERE tr.tag_id = p_tag_id
      AND tr.relation_type = 'PRIMARY'
      AND tr.dependent_tag_id <> p_new_primary;
END;
$$;

CREATE OR REPLACE FUNCTION sync_tag_dependencies(
    p_tag_id int,
    p_new_dependency_ids int[] DEFAULT NULL
) RETURNS void
LANGUAGE sql
AS $$
    WITH
        -- 把数组摊平为多行。若传 NULL，则 CTE 为空集
        new_deps AS (
            SELECT p_tag_id AS tag_id,
                   unnest(p_new_dependency_ids)::int AS dependent_tag_id
            WHERE p_new_dependency_ids IS NOT NULL
        ),
        -- 1) UPSERT：把传入集合中的项设为 DEPENDENCY
        upsert_deps AS (
            INSERT INTO tag_relations (tag_id, dependent_tag_id, relation_type)
            SELECT tag_id, dependent_tag_id, 'DEPENDENCY'
            FROM new_deps
            ON CONFLICT (tag_id, dependent_tag_id)
            DO UPDATE SET relation_type = 'DEPENDENCY'
            RETURNING 1
        )
    -- 2) 删除不在传入集合里的旧 DEPENDENCY（仅当传入不是 NULL 才执行删除）
    DELETE FROM tag_relations tr
    WHERE tr.tag_id = p_tag_id
      AND tr.relation_type = 'DEPENDENCY'
      AND p_new_dependency_ids IS NOT NULL
      AND NOT EXISTS (
            SELECT 1 FROM new_deps nd
            WHERE nd.dependent_tag_id = tr.dependent_tag_id
        );
$$;

--- Create Registered Nodes

CREATE TABLE IF NOT EXISTS registered_nodes (
    tag_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    client_node_id INTEGER NOT NULL,
    params JSONB NOT NULL DEFAULT '{}',
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);