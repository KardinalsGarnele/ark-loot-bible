PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS creature_components (
  creature_component_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
  creature_id TEXT NOT NULL REFERENCES creatures(creature_id),
  component_type TEXT NOT NULL CHECK(component_type IN ('VARIANTS','MAP_PRESENCE','SPAWNS','TAMING','BREEDING','STATS','DROPS','HARVEST','SADDLE','DOSSIER')),
  display_name TEXT NOT NULL,
  component_status TEXT NOT NULL DEFAULT 'EMPTY' CHECK(component_status IN ('EMPTY','PARTIAL','COMPLETE')),
  verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
  notes TEXT,
  UNIQUE(creature_id,component_type)
);
CREATE TABLE IF NOT EXISTS creature_content_imports (
  creature_content_import_id TEXT PRIMARY KEY,
  manifest_sha256 TEXT NOT NULL UNIQUE,
  creature_id TEXT NOT NULL REFERENCES creatures(creature_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  import_status TEXT NOT NULL CHECK(import_status IN ('IMPORTED','NO_CHANGES','FAILED')),
  imported_at TEXT NOT NULL,
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_creature_components_creature ON creature_components(creature_id,component_type);
