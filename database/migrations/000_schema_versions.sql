-- Schema version tracking table
-- Ensures migrations are applied in correct order and tracks database state

CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum TEXT,
    execution_time_ms INTEGER
);

-- Initial schema version
INSERT INTO schema_versions (version, description, applied_at) VALUES 
(0, 'Initial schema creation', NOW())
ON CONFLICT DO NOTHING;