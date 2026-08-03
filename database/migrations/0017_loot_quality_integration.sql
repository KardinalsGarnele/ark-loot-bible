
PRAGMA foreign_keys = ON;

ALTER TABLE loot_sources ADD COLUMN drop_color TEXT;
ALTER TABLE loot_sources ADD COLUMN has_ring INTEGER;
ALTER TABLE loot_sources ADD COLUMN required_level INTEGER;
ALTER TABLE loot_sources ADD COLUMN quality_profile_id TEXT REFERENCES quality_profiles(quality_profile_id);

ALTER TABLE loot_entries ADD COLUMN item_quality_multiplier_percent REAL;
ALTER TABLE loot_entries ADD COLUMN calculated_quality_min_percent REAL;
ALTER TABLE loot_entries ADD COLUMN calculated_quality_max_percent REAL;
ALTER TABLE loot_entries ADD COLUMN quality_formula_version TEXT;

CREATE TABLE IF NOT EXISTS loot_quality_recalculations (
  loot_quality_recalculation_id TEXT PRIMARY KEY,
  loot_source_id TEXT REFERENCES loot_sources(loot_source_id),
  quality_profile_id TEXT REFERENCES quality_profiles(quality_profile_id),
  entries_seen INTEGER NOT NULL,
  entries_calculated INTEGER NOT NULL,
  entries_incomplete INTEGER NOT NULL,
  recalculated_at TEXT NOT NULL,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_loot_sources_color_ring_level
ON loot_sources(drop_color, has_ring, required_level);

CREATE INDEX IF NOT EXISTS idx_loot_entries_quality_multiplier
ON loot_entries(item_quality_multiplier_percent);
