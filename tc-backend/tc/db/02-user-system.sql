-- User system migration
-- Stores Keycloak user info on nodes

ALTER TABLE nodes ALTER COLUMN creator_signature TYPE VARCHAR(255);
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS creator_name VARCHAR(255);
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'draft';
-- status values: draft, pending_review, published, archived
