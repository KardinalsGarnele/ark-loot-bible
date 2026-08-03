PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS canonical_revisions (
    revision_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    entity_type TEXT NOT NULL,
    revision_number INTEGER NOT NULL CHECK(revision_number > 0),
    review_case_id TEXT NOT NULL REFERENCES review_cases(review_case_id),
    operation TEXT NOT NULL CHECK(operation IN ('CREATE','UPDATE')),
    previous_snapshot_json TEXT,
    new_snapshot_json TEXT NOT NULL,
    promoted_by TEXT NOT NULL,
    promoted_at TEXT NOT NULL,
    UNIQUE(entity_id, revision_number),
    UNIQUE(review_case_id)
);

CREATE TABLE IF NOT EXISTS canonical_promotion_attempts (
    promotion_attempt_id TEXT PRIMARY KEY,
    review_case_id TEXT NOT NULL REFERENCES review_cases(review_case_id),
    entity_id TEXT,
    entity_type TEXT NOT NULL,
    attempt_mode TEXT NOT NULL CHECK(attempt_mode IN ('PREVIEW','COMMIT')),
    attempt_status TEXT NOT NULL CHECK(attempt_status IN ('SUCCEEDED','BLOCKED','FAILED','NO_CHANGES')),
    diff_json TEXT,
    actor TEXT NOT NULL,
    attempted_at TEXT NOT NULL,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_canonical_revisions_entity ON canonical_revisions(entity_id, revision_number DESC);
CREATE INDEX IF NOT EXISTS idx_promotion_attempts_case ON canonical_promotion_attempts(review_case_id, attempted_at DESC);
