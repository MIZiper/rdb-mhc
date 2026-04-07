ALTER TABLE nodes
ADD COLUMN backlink VARCHAR(255), -- link to analysis
ADD COLUMN frozenlink VARCHAR(255), -- link to release document
ADD COLUMN frozen BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN validate_key VARCHAR(20) DEFAULT NULL,
ADD COLUMN content JSONB NOT NULL DEFAULT '{}',
ADD COLUMN content_type VARCHAR(50); -- Scope-Type-SubType.v01