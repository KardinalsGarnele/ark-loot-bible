PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS content_manifests (
 content_manifest_id TEXT PRIMARY KEY, manifest_code TEXT NOT NULL UNIQUE,
 content_type TEXT NOT NULL, target_entity_type TEXT NOT NULL,
 source_id TEXT NOT NULL REFERENCES sources(source_id),
 source_version_id TEXT NOT NULL REFERENCES source_versions(source_version_id),
 game_version TEXT, schema_version TEXT NOT NULL, manifest_sha256 TEXT NOT NULL UNIQUE,
 manifest_status TEXT NOT NULL DEFAULT 'STAGED' CHECK(manifest_status IN ('STAGED','VALIDATED','IMPORTED','REJECTED')),
 created_at TEXT NOT NULL, imported_at TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS content_manifest_records (
 content_manifest_record_id TEXT PRIMARY KEY,
 content_manifest_id TEXT NOT NULL REFERENCES content_manifests(content_manifest_id),
 record_key TEXT NOT NULL, entity_type TEXT NOT NULL, proposed_entity_id TEXT,
 canonical_name TEXT NOT NULL, payload_json TEXT NOT NULL, record_sha256 TEXT NOT NULL,
 validation_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(validation_status IN ('PENDING','VALID','INVALID')),
 validation_errors_json TEXT, import_record_id TEXT REFERENCES import_records(import_record_id),
 UNIQUE(content_manifest_id,record_key));
CREATE TABLE IF NOT EXISTS map_components (
 map_component_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
 map_id TEXT NOT NULL REFERENCES maps(map_id),
 component_type TEXT NOT NULL CHECK(component_type IN ('REGION_COLLECTION','SPAWN_COLLECTION','LOOT_COLLECTION','CAVE_COLLECTION','ARTIFACT_COLLECTION','BOSS_COLLECTION','EXPLORER_NOTE_COLLECTION','RESOURCE_COLLECTION')),
 display_name TEXT NOT NULL, component_status TEXT NOT NULL DEFAULT 'EMPTY' CHECK(component_status IN ('EMPTY','PARTIAL','COMPLETE')),
 verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION', source_url TEXT, notes TEXT,
 UNIQUE(map_id,component_type));
CREATE TABLE IF NOT EXISTS content_import_runs (
 content_import_run_id TEXT PRIMARY KEY, content_manifest_id TEXT NOT NULL REFERENCES content_manifests(content_manifest_id),
 run_mode TEXT NOT NULL CHECK(run_mode IN ('DRY_RUN','COMMIT')),
 run_status TEXT NOT NULL CHECK(run_status IN ('STARTED','VALIDATED','COMPLETED','FAILED','NO_CHANGES')),
 records_seen INTEGER NOT NULL DEFAULT 0, records_valid INTEGER NOT NULL DEFAULT 0,
 records_invalid INTEGER NOT NULL DEFAULT 0, started_at TEXT NOT NULL, completed_at TEXT, error_message TEXT);
CREATE INDEX IF NOT EXISTS idx_content_manifest_records_manifest ON content_manifest_records(content_manifest_id);
CREATE INDEX IF NOT EXISTS idx_map_components_map ON map_components(map_id,component_type);
