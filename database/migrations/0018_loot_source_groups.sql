
PRAGMA foreign_keys = ON;

ALTER TABLE loot_sources ADD COLUMN source_group TEXT
  CHECK(source_group IS NULL OR source_group IN (
    'SURFACE_SUPPLY','CAVE','DEEP_SEA','FISHING','CREATURE_DROP',
    'BOSS_TEK','MISSION','OSD','WORLD','OTHER'
  ));

ALTER TABLE loot_sources ADD COLUMN display_order INTEGER;

CREATE TABLE IF NOT EXISTS map_loot_group_status (
  map_loot_group_status_id TEXT PRIMARY KEY,
  map_id TEXT NOT NULL REFERENCES maps(map_id),
  source_group TEXT NOT NULL CHECK(source_group IN (
    'SURFACE_SUPPLY','CAVE','DEEP_SEA','FISHING','CREATURE_DROP',
    'BOSS_TEK','MISSION','OSD','WORLD','OTHER'
  )),
  group_status TEXT NOT NULL DEFAULT 'EMPTY'
    CHECK(group_status IN ('EMPTY','PARTIAL','COMPLETE')),
  verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
  notes TEXT,
  UNIQUE(map_id, source_group)
);

CREATE INDEX IF NOT EXISTS idx_loot_sources_group
ON loot_sources(map_id, source_group, display_order);

CREATE INDEX IF NOT EXISTS idx_map_loot_group_status
ON map_loot_group_status(map_id, source_group);
