PRAGMA foreign_keys = ON;

-- Sprint 002: registry, lifecycle, relationships, map scope, and spawn normalization.

CREATE TABLE IF NOT EXISTS id_registry (
    entity_type TEXT PRIMARY KEY,
    id_prefix TEXT NOT NULL UNIQUE,
    next_sequence INTEGER NOT NULL DEFAULT 1 CHECK (next_sequence > 0),
    width INTEGER NOT NULL DEFAULT 6 CHECK (width BETWEEN 4 AND 12),
    description TEXT
);

CREATE TABLE IF NOT EXISTS entity_aliases (
    alias_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    alias TEXT NOT NULL,
    locale TEXT,
    alias_type TEXT NOT NULL DEFAULT 'DISPLAY_NAME',
    valid_from TEXT,
    valid_to TEXT,
    UNIQUE(entity_id, alias, locale, alias_type)
);

CREATE TABLE IF NOT EXISTS entity_relationships (
    relationship_id TEXT PRIMARY KEY,
    subject_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    predicate TEXT NOT NULL,
    object_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    valid_from TEXT,
    valid_to TEXT,
    notes TEXT,
    CHECK(subject_entity_id <> object_entity_id),
    UNIQUE(subject_entity_id, predicate, object_entity_id, valid_from)
);

CREATE TABLE IF NOT EXISTS map_scope (
    scope_id TEXT PRIMARY KEY,
    map_name TEXT NOT NULL UNIQUE,
    scope_status TEXT NOT NULL DEFAULT 'PLANNED',
    official_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    canonical_map_id TEXT REFERENCES maps(map_id),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS spawn_regions (
    spawn_region_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    map_id TEXT NOT NULL REFERENCES maps(map_id),
    internal_name TEXT,
    display_name TEXT,
    geometry_type TEXT,
    geometry_json TEXT
);

CREATE TABLE IF NOT EXISTS spawn_containers (
    spawn_container_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    map_id TEXT REFERENCES maps(map_id),
    internal_name TEXT,
    container_class_path TEXT
);

CREATE TABLE IF NOT EXISTS creature_spawn_entries (
    spawn_entry_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    variant_id TEXT NOT NULL REFERENCES creature_variants(variant_id),
    spawn_container_id TEXT REFERENCES spawn_containers(spawn_container_id),
    spawn_region_id TEXT REFERENCES spawn_regions(spawn_region_id),
    spawn_weight REAL,
    min_percentage REAL,
    max_percentage REAL,
    verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION'
);

CREATE TABLE IF NOT EXISTS data_releases (
    release_id TEXT PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    released_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    data_version TEXT NOT NULL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_slug ON entities(slug);
CREATE INDEX IF NOT EXISTS idx_evidence_entity ON evidence(entity_id);
CREATE INDEX IF NOT EXISTS idx_relationship_subject ON entity_relationships(subject_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationship_object ON entity_relationships(object_entity_id);
CREATE INDEX IF NOT EXISTS idx_spawn_entry_variant ON creature_spawn_entries(variant_id);
