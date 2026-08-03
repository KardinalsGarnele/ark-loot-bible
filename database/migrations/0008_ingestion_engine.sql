PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ingestion_runs (
  run_id TEXT PRIMARY KEY,
  adapter_name TEXT NOT NULL,
  source_id TEXT,
  source_version_id TEXT,
  input_uri TEXT NOT NULL,
  input_sha256 TEXT NOT NULL,
  mode TEXT NOT NULL CHECK(mode IN ('DRY_RUN','COMMIT')),
  status TEXT NOT NULL CHECK(status IN ('STARTED','VALIDATED','COMPLETED','FAILED','NO_CHANGES')),
  records_seen INTEGER NOT NULL DEFAULT 0,
  records_accepted INTEGER NOT NULL DEFAULT 0,
  records_rejected INTEGER NOT NULL DEFAULT 0,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  error_message TEXT,
  FOREIGN KEY(source_id) REFERENCES sources(source_id),
  FOREIGN KEY(source_version_id) REFERENCES source_versions(source_version_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ingestion_commit_content
ON ingestion_runs(adapter_name, input_sha256, mode)
WHERE mode='COMMIT' AND status='COMPLETED';

CREATE TABLE IF NOT EXISTS ingestion_messages (
  message_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  record_key TEXT,
  severity TEXT NOT NULL CHECK(severity IN ('INFO','WARNING','ERROR')),
  code TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(run_id) REFERENCES ingestion_runs(run_id) ON DELETE CASCADE
);
