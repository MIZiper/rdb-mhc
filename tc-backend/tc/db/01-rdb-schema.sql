ALTER TABLE nodes
ADD COLUMN backlink VARCHAR(255), -- link to analysis
ADD COLUMN frozenlink VARCHAR(255), -- link to release document
ADD COLUMN frozen BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN validate_key VARCHAR(20) DEFAULT NULL;
