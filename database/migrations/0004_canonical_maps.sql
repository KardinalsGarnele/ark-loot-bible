PRAGMA foreign_keys = ON;

-- Sprint 004: canonical map domain and field-level evidence links.
ALTER TABLE maps ADD COLUMN game_title TEXT;
ALTER TABLE maps ADD COLUMN map_kind TEXT;
ALTER TABLE maps ADD COLUMN included_with_base_game INTEGER;
ALTER TABLE maps ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE';

CREATE TABLE IF NOT EXISTS field_evidence_links (
    field_evidence_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    field_name TEXT NOT NULL,
    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
    is_current INTEGER NOT NULL DEFAULT 1 CHECK(is_current IN (0,1)),
    linked_at TEXT NOT NULL,
    UNIQUE(entity_id, field_name, evidence_id)
);

CREATE TABLE IF NOT EXISTS canonical_map_imports (
    canonical_map_import_id TEXT PRIMARY KEY,
    import_record_id TEXT NOT NULL UNIQUE REFERENCES import_records(import_record_id),
    map_id TEXT NOT NULL UNIQUE REFERENCES maps(map_id),
    policy_version TEXT NOT NULL,
    promoted_at TEXT NOT NULL,
    promoted_by TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_field_evidence_entity_field ON field_evidence_links(entity_id, field_name);
