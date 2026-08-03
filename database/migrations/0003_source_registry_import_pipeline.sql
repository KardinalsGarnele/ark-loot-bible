PRAGMA foreign_keys = ON;

-- Sprint 003: evidence-first source registry and canonical import pipeline.

CREATE TABLE IF NOT EXISTS source_versions (
    source_version_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    version_label TEXT,
    content_hash_sha256 TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    effective_from TEXT,
    effective_to TEXT,
    local_snapshot_path TEXT,
    UNIQUE(source_id, content_hash_sha256)
);

CREATE TABLE IF NOT EXISTS import_batches (
    import_batch_id TEXT PRIMARY KEY,
    source_version_id TEXT NOT NULL REFERENCES source_versions(source_version_id),
    importer_name TEXT NOT NULL,
    importer_version TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    batch_status TEXT NOT NULL DEFAULT 'STAGED'
        CHECK(batch_status IN ('STAGED','VALIDATED','PARTIALLY_PROMOTED','PROMOTED','REJECTED')),
    record_count INTEGER NOT NULL DEFAULT 0 CHECK(record_count >= 0),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS import_records (
    import_record_id TEXT PRIMARY KEY,
    import_batch_id TEXT NOT NULL REFERENCES import_batches(import_batch_id),
    source_row_key TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    proposed_entity_id TEXT,
    proposed_canonical_name TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    record_status TEXT NOT NULL DEFAULT 'STAGED'
        CHECK(record_status IN ('STAGED','VALID','QUARANTINED','PROMOTED','REJECTED')),
    validation_errors_json TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(import_batch_id, source_row_key)
);

CREATE TABLE IF NOT EXISTS claim_candidates (
    claim_candidate_id TEXT PRIMARY KEY,
    import_record_id TEXT NOT NULL REFERENCES import_records(import_record_id),
    field_name TEXT NOT NULL,
    claim_value TEXT,
    evidence_strength TEXT NOT NULL DEFAULT 'UNASSESSED'
        CHECK(evidence_strength IN ('UNASSESSED','PRIMARY','SECONDARY','COMMUNITY','CONFLICTING')),
    proposed_verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    candidate_status TEXT NOT NULL DEFAULT 'STAGED'
        CHECK(candidate_status IN ('STAGED','VALID','QUARANTINED','PROMOTED','REJECTED')),
    notes TEXT,
    UNIQUE(import_record_id, field_name, claim_value)
);

CREATE TABLE IF NOT EXISTS quarantine_records (
    quarantine_id TEXT PRIMARY KEY,
    import_record_id TEXT NOT NULL REFERENCES import_records(import_record_id),
    reason_code TEXT NOT NULL,
    reason_detail TEXT NOT NULL,
    quarantined_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT,
    UNIQUE(import_record_id, reason_code)
);

CREATE TABLE IF NOT EXISTS promotion_log (
    promotion_id TEXT PRIMARY KEY,
    import_record_id TEXT NOT NULL REFERENCES import_records(import_record_id),
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    promoted_at TEXT NOT NULL,
    promoted_by TEXT NOT NULL,
    decision_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_source_versions_source ON source_versions(source_id);
CREATE INDEX IF NOT EXISTS idx_import_records_batch ON import_records(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_import_records_status ON import_records(record_status);
CREATE INDEX IF NOT EXISTS idx_claim_candidates_record ON claim_candidates(import_record_id);
CREATE INDEX IF NOT EXISTS idx_quarantine_unresolved ON quarantine_records(resolved_at);
