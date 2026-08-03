PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS item_components (
  item_component_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
  item_id TEXT NOT NULL REFERENCES items(item_id),
  component_type TEXT NOT NULL CHECK(component_type IN (
    'CLASSIFICATION','BLUEPRINTS','CRAFTING','REPAIR','LOOT',
    'CREATURE_USE','MAP_AVAILABILITY','TECHNICAL'
  )),
  display_name TEXT NOT NULL,
  component_status TEXT NOT NULL DEFAULT 'EMPTY'
    CHECK(component_status IN ('EMPTY','PARTIAL','COMPLETE')),
  verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
  notes TEXT,
  UNIQUE(item_id, component_type)
);

CREATE TABLE IF NOT EXISTS item_content_imports (
  item_content_import_id TEXT PRIMARY KEY,
  manifest_sha256 TEXT NOT NULL UNIQUE,
  item_id TEXT NOT NULL REFERENCES items(item_id),
  blueprint_id TEXT REFERENCES blueprints(blueprint_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  import_status TEXT NOT NULL CHECK(import_status IN ('IMPORTED','NO_CHANGES','FAILED')),
  imported_at TEXT NOT NULL,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_item_components_item
ON item_components(item_id, component_type);
