PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS review_cases (
    review_case_id TEXT PRIMARY KEY,
    import_record_id TEXT NOT NULL UNIQUE REFERENCES import_records(import_record_id),
    entity_type TEXT NOT NULL,
    proposed_entity_id TEXT,
    proposed_canonical_name TEXT NOT NULL,
    case_status TEXT NOT NULL DEFAULT 'OPEN'
      CHECK(case_status IN ('OPEN','IN_REVIEW','APPROVED','REJECTED','CONFLICT','PROMOTED')),
    priority INTEGER NOT NULL DEFAULT 50 CHECK(priority BETWEEN 0 AND 100),
    assigned_to TEXT,
    opened_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT,
    row_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS review_decisions (
    review_decision_id TEXT PRIMARY KEY,
    review_case_id TEXT NOT NULL REFERENCES review_cases(review_case_id),
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('APPROVE','REJECT','REQUEST_CHANGES','MARK_CONFLICT')),
    notes TEXT,
    decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_reviews (
    claim_review_id TEXT PRIMARY KEY,
    review_case_id TEXT NOT NULL REFERENCES review_cases(review_case_id),
    claim_candidate_id TEXT NOT NULL REFERENCES claim_candidates(claim_candidate_id),
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('ACCEPT','REJECT','CONFLICT')),
    normalized_value TEXT,
    notes TEXT,
    reviewed_at TEXT NOT NULL,
    UNIQUE(review_case_id, claim_candidate_id, reviewer)
);

CREATE TABLE IF NOT EXISTS claim_conflicts (
    claim_conflict_id TEXT PRIMARY KEY,
    review_case_id TEXT NOT NULL REFERENCES review_cases(review_case_id),
    field_name TEXT NOT NULL,
    left_claim_candidate_id TEXT NOT NULL REFERENCES claim_candidates(claim_candidate_id),
    right_claim_candidate_id TEXT NOT NULL REFERENCES claim_candidates(claim_candidate_id),
    conflict_status TEXT NOT NULL DEFAULT 'OPEN' CHECK(conflict_status IN ('OPEN','RESOLVED','IGNORED')),
    resolution_notes TEXT,
    resolved_by TEXT,
    resolved_at TEXT,
    UNIQUE(review_case_id, left_claim_candidate_id, right_claim_candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_review_cases_status ON review_cases(case_status, priority DESC, opened_at);
CREATE INDEX IF NOT EXISTS idx_review_cases_assignee ON review_cases(assigned_to, case_status);
CREATE INDEX IF NOT EXISTS idx_claim_reviews_case ON claim_reviews(review_case_id);
CREATE INDEX IF NOT EXISTS idx_claim_conflicts_case ON claim_conflicts(review_case_id, conflict_status);
