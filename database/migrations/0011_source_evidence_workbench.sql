PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_health_checks (
    source_health_check_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    checked_at TEXT NOT NULL,
    check_status TEXT NOT NULL CHECK(check_status IN ('HEALTHY','DEGRADED','UNREACHABLE','UNKNOWN')),
    http_status INTEGER,
    response_time_ms INTEGER,
    content_hash_sha256 TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS claim_source_evidence (
    claim_source_evidence_id TEXT PRIMARY KEY,
    claim_candidate_id TEXT NOT NULL REFERENCES claim_candidates(claim_candidate_id),
    source_version_id TEXT NOT NULL REFERENCES source_versions(source_version_id),
    evidence_relation TEXT NOT NULL DEFAULT 'SUPPORTS'
      CHECK(evidence_relation IN ('SUPPORTS','CONTRADICTS','CONTEXT')),
    locator TEXT,
    excerpt TEXT,
    linked_by TEXT NOT NULL,
    linked_at TEXT NOT NULL,
    UNIQUE(claim_candidate_id, source_version_id, evidence_relation, locator)
);

CREATE TABLE IF NOT EXISTS source_version_comparisons (
    source_version_comparison_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    left_source_version_id TEXT NOT NULL REFERENCES source_versions(source_version_id),
    right_source_version_id TEXT NOT NULL REFERENCES source_versions(source_version_id),
    changed INTEGER NOT NULL CHECK(changed IN (0,1)),
    summary_json TEXT NOT NULL,
    compared_by TEXT NOT NULL,
    compared_at TEXT NOT NULL,
    UNIQUE(left_source_version_id, right_source_version_id)
);

CREATE INDEX IF NOT EXISTS idx_source_health_checks_source
  ON source_health_checks(source_id, checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_claim_source_evidence_claim
  ON claim_source_evidence(claim_candidate_id, linked_at DESC);
CREATE INDEX IF NOT EXISTS idx_source_version_comparisons_source
  ON source_version_comparisons(source_id, compared_at DESC);
