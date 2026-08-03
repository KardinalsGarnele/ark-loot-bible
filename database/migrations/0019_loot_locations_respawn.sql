
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS map_regions (
  map_region_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
  map_id TEXT NOT NULL REFERENCES maps(map_id),
  region_code TEXT,
  display_name TEXT NOT NULL,
  geometry_type TEXT NOT NULL DEFAULT 'UNKNOWN'
    CHECK(geometry_type IN ('POINT','POLYGON','LINE','AREA_LABEL','UNKNOWN')),
  geometry_json TEXT,
  verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
  source_url TEXT,
  notes TEXT,
  UNIQUE(map_id, display_name)
);

CREATE TABLE IF NOT EXISTS loot_source_locations (
  loot_source_location_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
  loot_source_id TEXT NOT NULL REFERENCES loot_sources(loot_source_id),
  map_id TEXT NOT NULL REFERENCES maps(map_id),
  map_region_id TEXT REFERENCES map_regions(map_region_id),
  location_type TEXT NOT NULL
    CHECK(location_type IN ('FIXED_POINT','REGION','ROUTE','RANDOM_WORLD','MOVING','UNKNOWN')),
  latitude REAL,
  longitude REAL,
  altitude REAL,
  coordinate_precision TEXT
    CHECK(coordinate_precision IS NULL OR coordinate_precision IN ('EXACT','APPROXIMATE','REGION_ONLY','UNKNOWN')),
  geometry_json TEXT,
  verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
  source_url TEXT,
  notes TEXT,
  CHECK(latitude IS NULL OR (latitude >= 0 AND latitude <= 100)),
  CHECK(longitude IS NULL OR (longitude >= 0 AND longitude <= 100))
);

CREATE TABLE IF NOT EXISTS loot_source_respawn_profiles (
  loot_source_respawn_profile_id TEXT PRIMARY KEY,
  loot_source_id TEXT NOT NULL REFERENCES loot_sources(loot_source_id),
  respawn_mode TEXT NOT NULL
    CHECK(respawn_mode IN ('FIXED','RANGE','CONDITIONAL','GLOBAL_POOL','UNKNOWN')),
  minimum_seconds INTEGER,
  maximum_seconds INTEGER,
  initial_spawn_seconds INTEGER,
  active_limit INTEGER,
  requires_pickup INTEGER,
  requires_player_distance INTEGER,
  verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
  source_url TEXT,
  notes TEXT,
  CHECK(minimum_seconds IS NULL OR minimum_seconds >= 0),
  CHECK(maximum_seconds IS NULL OR maximum_seconds >= minimum_seconds),
  CHECK(initial_spawn_seconds IS NULL OR initial_spawn_seconds >= 0),
  CHECK(active_limit IS NULL OR active_limit >= 0),
  UNIQUE(loot_source_id)
);

CREATE INDEX IF NOT EXISTS idx_map_regions_map
ON map_regions(map_id, display_name);

CREATE INDEX IF NOT EXISTS idx_loot_source_locations_source
ON loot_source_locations(loot_source_id, location_type);

CREATE INDEX IF NOT EXISTS idx_loot_source_locations_map
ON loot_source_locations(map_id, map_region_id);

CREATE INDEX IF NOT EXISTS idx_loot_source_respawn
ON loot_source_respawn_profiles(loot_source_id);
