
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS loot_content_imports (
  loot_content_import_id TEXT PRIMARY KEY,
  manifest_sha256 TEXT NOT NULL UNIQUE,
  loot_source_id TEXT NOT NULL REFERENCES loot_sources(loot_source_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  import_status TEXT NOT NULL CHECK(import_status IN ('IMPORTED','NO_CHANGES','FAILED')),
  imported_at TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS loot_content_components (
  loot_content_component_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
  loot_source_id TEXT NOT NULL REFERENCES loot_sources(loot_source_id),
  component_type TEXT NOT NULL CHECK(component_type IN (
    'IDENTITY','QUALITY_PROFILE','RESPAWN','LOOT_SETS','LOOT_ENTRIES',
    'MAP_RELATION','COORDINATES','TECHNICAL'
  )),
  display_name TEXT NOT NULL,
  component_status TEXT NOT NULL DEFAULT 'EMPTY'
    CHECK(component_status IN ('EMPTY','PARTIAL','COMPLETE')),
  verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
  notes TEXT,
  UNIQUE(loot_source_id, component_type)
);

CREATE INDEX IF NOT EXISTS idx_loot_content_components_source
ON loot_content_components(loot_source_id, component_type);
