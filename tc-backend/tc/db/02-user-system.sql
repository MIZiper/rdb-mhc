-- User system migration
-- Stores Keycloak user info on nodes

ALTER TABLE nodes ALTER COLUMN creator_signature TYPE VARCHAR(255);
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'nodes' AND column_name = 'creator_signature'
    ) THEN
        ALTER TABLE nodes RENAME COLUMN creator_signature TO creator_sub;
    END IF;
END $$;
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS creator_name VARCHAR(255);
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'draft';
-- status values: draft, pending_review, published, archived
