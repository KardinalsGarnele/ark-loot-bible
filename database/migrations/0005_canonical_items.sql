PRAGMA foreign_keys = ON;

ALTER TABLE items ADD COLUMN game_title TEXT;
ALTER TABLE items ADD COLUMN internal_name TEXT;
ALTER TABLE items ADD COLUMN description TEXT;
ALTER TABLE items ADD COLUMN stack_size INTEGER CHECK(stack_size IS NULL OR stack_size > 0);
ALTER TABLE items ADD COLUMN weight REAL CHECK(weight IS NULL OR weight >= 0);
ALTER TABLE items ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE';

CREATE TABLE IF NOT EXISTS item_categories (
    category_code TEXT PRIMARY KEY,
    display_name TEXT NOT NULL UNIQUE,
    parent_category_code TEXT REFERENCES item_categories(category_code),
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS item_category_assignments (
    item_id TEXT NOT NULL REFERENCES items(item_id),
    category_code TEXT NOT NULL REFERENCES item_categories(category_code),
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK(is_primary IN (0,1)),
    assigned_at TEXT NOT NULL,
    PRIMARY KEY (item_id, category_code)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_item_one_primary_category
ON item_category_assignments(item_id)
WHERE is_primary = 1;

CREATE TABLE IF NOT EXISTS item_relationships (
    item_relationship_id TEXT PRIMARY KEY,
    source_item_id TEXT NOT NULL REFERENCES items(item_id),
    relationship_type TEXT NOT NULL,
    target_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    valid_from TEXT,
    valid_to TEXT,
    verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    created_at TEXT NOT NULL,
    UNIQUE(source_item_id, relationship_type, target_entity_id, valid_from)
);

CREATE TABLE IF NOT EXISTS crafting_recipes (
    recipe_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
    output_item_id TEXT NOT NULL REFERENCES items(item_id),
    output_quantity INTEGER NOT NULL DEFAULT 1 CHECK(output_quantity > 0),
    crafting_station_entity_id TEXT REFERENCES entities(entity_id)
);

CREATE TABLE IF NOT EXISTS crafting_ingredients (
    recipe_id TEXT NOT NULL REFERENCES crafting_recipes(recipe_id),
    ingredient_item_id TEXT NOT NULL REFERENCES items(item_id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    PRIMARY KEY(recipe_id, ingredient_item_id)
);

CREATE TABLE IF NOT EXISTS canonical_item_imports (
    canonical_item_import_id TEXT PRIMARY KEY,
    import_record_id TEXT NOT NULL UNIQUE REFERENCES import_records(import_record_id),
    item_id TEXT NOT NULL UNIQUE REFERENCES items(item_id),
    policy_version TEXT NOT NULL,
    promoted_at TEXT NOT NULL,
    promoted_by TEXT NOT NULL
);
