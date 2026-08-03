PRAGMA foreign_keys = ON;

ALTER TABLE creatures ADD COLUMN game_title TEXT;
ALTER TABLE creatures ADD COLUMN internal_name TEXT;
ALTER TABLE creatures ADD COLUMN description TEXT;
ALTER TABLE creatures ADD COLUMN diet_type TEXT;
ALTER TABLE creatures ADD COLUMN temperament TEXT;
ALTER TABLE creatures ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE';

ALTER TABLE creature_variants ADD COLUMN internal_name TEXT;
ALTER TABLE creature_variants ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0 CHECK(is_default IN (0,1));
ALTER TABLE creature_variants ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE';

CREATE UNIQUE INDEX IF NOT EXISTS idx_creature_default_variant
ON creature_variants(creature_id) WHERE is_default = 1;

CREATE TABLE IF NOT EXISTS creature_map_presence (
    creature_id TEXT NOT NULL REFERENCES creatures(creature_id),
    map_id TEXT NOT NULL REFERENCES maps(map_id),
    presence_type TEXT NOT NULL DEFAULT 'SPAWNS',
    verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    valid_from TEXT,
    valid_to TEXT,
    PRIMARY KEY (creature_id, map_id, presence_type, valid_from)
);

CREATE TABLE IF NOT EXISTS creature_relationships (
    creature_relationship_id TEXT PRIMARY KEY,
    source_creature_id TEXT NOT NULL REFERENCES creatures(creature_id),
    relationship_type TEXT NOT NULL,
    target_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    valid_from TEXT,
    valid_to TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(source_creature_id, relationship_type, target_entity_id, valid_from)
);

CREATE INDEX IF NOT EXISTS idx_creature_map_presence_creature ON creature_map_presence(creature_id);
CREATE INDEX IF NOT EXISTS idx_creature_relationships_source ON creature_relationships(source_creature_id);
