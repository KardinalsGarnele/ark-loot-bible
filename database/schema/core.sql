PRAGMA foreign_keys = ON;

CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    slug TEXT,
    verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT
);

CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    locator TEXT,
    publisher TEXT,
    captured_at TEXT,
    notes TEXT
);

CREATE TABLE evidence (
    evidence_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    field_name TEXT,
    claim_value TEXT,
    verification_status TEXT NOT NULL,
    valid_from TEXT,
    valid_to TEXT,
    notes TEXT
);

CREATE TABLE maps (
    map_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    internal_name TEXT,
    release_status TEXT,
    official INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE creatures (
    creature_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    species_name TEXT,
    tameable INTEGER,
    breedable INTEGER
);

CREATE TABLE creature_variants (
    variant_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    creature_id TEXT NOT NULL REFERENCES creatures(creature_id),
    variant_type TEXT NOT NULL
);

CREATE TABLE items (
    item_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    item_category TEXT,
    quality_capable INTEGER
);

CREATE TABLE blueprints (
    blueprint_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    item_id TEXT NOT NULL REFERENCES items(item_id),
    blueprint_type TEXT,
    can_be_looted INTEGER,
    can_be_crafted INTEGER
);

CREATE TABLE loot_sources (
    loot_source_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    map_id TEXT REFERENCES maps(map_id),
    source_type TEXT NOT NULL
);

CREATE TABLE loot_sets (
    loot_set_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    loot_source_id TEXT NOT NULL REFERENCES loot_sources(loot_source_id)
);

CREATE TABLE loot_entries (
    loot_entry_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    loot_set_id TEXT NOT NULL REFERENCES loot_sets(loot_set_id),
    item_id TEXT REFERENCES items(item_id),
    blueprint_id TEXT REFERENCES blueprints(blueprint_id),
    effective_quality_min REAL,
    effective_quality_max REAL
);

CREATE TABLE creature_spawns (
    spawn_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    variant_id TEXT NOT NULL REFERENCES creature_variants(variant_id),
    map_id TEXT NOT NULL REFERENCES maps(map_id),
    region_name TEXT,
    spawn_container_name TEXT,
    geometry_json TEXT,
    spawn_weight REAL
);
