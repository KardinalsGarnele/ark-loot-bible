PRAGMA foreign_keys = ON;

ALTER TABLE blueprints ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE blueprints ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION';
ALTER TABLE loot_sources ADD COLUMN internal_name TEXT;
ALTER TABLE loot_sources ADD COLUMN description TEXT;
ALTER TABLE loot_sources ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE loot_sources ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION';
ALTER TABLE loot_sets ADD COLUMN selection_weight REAL CHECK(selection_weight IS NULL OR selection_weight >= 0);
ALTER TABLE loot_sets ADD COLUMN min_rolls INTEGER CHECK(min_rolls IS NULL OR min_rolls >= 0);
ALTER TABLE loot_sets ADD COLUMN max_rolls INTEGER CHECK(max_rolls IS NULL OR max_rolls >= min_rolls);
ALTER TABLE loot_sets ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION';
ALTER TABLE loot_entries ADD COLUMN entry_weight REAL CHECK(entry_weight IS NULL OR entry_weight >= 0);
ALTER TABLE loot_entries ADD COLUMN min_quantity INTEGER CHECK(min_quantity IS NULL OR min_quantity >= 0);
ALTER TABLE loot_entries ADD COLUMN max_quantity INTEGER CHECK(max_quantity IS NULL OR max_quantity >= min_quantity);
ALTER TABLE loot_entries ADD COLUMN blueprint_chance REAL CHECK(blueprint_chance IS NULL OR (blueprint_chance >= 0 AND blueprint_chance <= 1));
ALTER TABLE loot_entries ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION';

CREATE TABLE loot_source_relationships (
    relationship_id TEXT PRIMARY KEY,
    source_loot_source_id TEXT NOT NULL REFERENCES loot_sources(loot_source_id),
    relationship_type TEXT NOT NULL,
    target_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    valid_from TEXT,
    valid_to TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(source_loot_source_id, relationship_type, target_entity_id, valid_from)
);

CREATE INDEX idx_loot_sets_source ON loot_sets(loot_source_id);
CREATE INDEX idx_loot_entries_set ON loot_entries(loot_set_id);
CREATE INDEX idx_loot_entries_item ON loot_entries(item_id);
CREATE INDEX idx_loot_entries_blueprint ON loot_entries(blueprint_id);
