
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS quality_profiles (
  quality_profile_id TEXT PRIMARY KEY,
  profile_code TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  source_quality_min_percent REAL,
  source_quality_max_percent REAL,
  difficulty_multiplier REAL,
  crate_quality_multiplier REAL,
  rounding_digits INTEGER NOT NULL DEFAULT 2,
  verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
  source_url TEXT,
  notes TEXT,
  CHECK(source_quality_min_percent IS NULL OR source_quality_min_percent >= 0),
  CHECK(source_quality_max_percent IS NULL OR source_quality_max_percent >= source_quality_min_percent),
  CHECK(difficulty_multiplier IS NULL OR difficulty_multiplier >= 0),
  CHECK(crate_quality_multiplier IS NULL OR crate_quality_multiplier >= 0)
);

CREATE TABLE IF NOT EXISTS quality_calculation_runs (
  quality_calculation_run_id TEXT PRIMARY KEY,
  quality_profile_id TEXT REFERENCES quality_profiles(quality_profile_id),
  source_quality_min_percent REAL,
  source_quality_max_percent REAL,
  item_quality_multiplier_percent REAL,
  additional_multiplier REAL,
  result_min_percent REAL,
  result_max_percent REAL,
  rounding_digits INTEGER NOT NULL,
  formula_version TEXT NOT NULL,
  calculated_at TEXT NOT NULL,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_quality_calculation_runs_profile
ON quality_calculation_runs(quality_profile_id, calculated_at DESC);
