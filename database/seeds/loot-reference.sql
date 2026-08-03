-- Development-only graph. Names describe intent, not verified gameplay availability.
INSERT OR IGNORE INTO entities VALUES ('ITEM-000001','ITEM','Rex Saddle (Development Reference)','rex-saddle-reference','NEEDS_VERIFICATION',datetime('now'),datetime('now'),NULL);
INSERT OR IGNORE INTO items(item_id,item_category,quality_capable,game_title,description,lifecycle_status)
VALUES ('ITEM-000001','SADDLE',1,'ARK: Survival Ascended','Development reference item; all gameplay properties require evidence.','ACTIVE');
INSERT OR IGNORE INTO item_category_assignments(item_id,category_code,is_primary,assigned_at)
VALUES ('ITEM-000001','SADDLE',1,datetime('now'));

INSERT OR IGNORE INTO entities VALUES ('BP-000001','BLUEPRINT','Rex Saddle Blueprint (Development Reference)','rex-saddle-blueprint-reference','NEEDS_VERIFICATION',datetime('now'),datetime('now'),NULL);
INSERT OR IGNORE INTO blueprints(blueprint_id,item_id,blueprint_type,can_be_looted,can_be_crafted,verification_status)
VALUES ('BP-000001','ITEM-000001','ITEM_BLUEPRINT',NULL,NULL,'NEEDS_VERIFICATION');

INSERT OR IGNORE INTO entities VALUES ('LOOTSOURCE-000001','LOOT_SOURCE','Development Loot Source','development-loot-source','NEEDS_VERIFICATION',datetime('now'),datetime('now'),NULL);
INSERT OR IGNORE INTO loot_sources(loot_source_id,map_id,source_type,description,verification_status)
VALUES ('LOOTSOURCE-000001',NULL,'REFERENCE','Structural proof-of-concept only.','NEEDS_VERIFICATION');

INSERT OR IGNORE INTO entities VALUES ('LOOTSET-000001','LOOT_SET','Development Loot Set','development-loot-set','NEEDS_VERIFICATION',datetime('now'),datetime('now'),NULL);
INSERT OR IGNORE INTO loot_sets(loot_set_id,loot_source_id,verification_status)
VALUES ('LOOTSET-000001','LOOTSOURCE-000001','NEEDS_VERIFICATION');

INSERT OR IGNORE INTO entities VALUES ('LOOTENTRY-000001','LOOT_ENTRY','Development Rex Saddle Blueprint Entry','development-rex-saddle-blueprint-entry','NEEDS_VERIFICATION',datetime('now'),datetime('now'),NULL);
INSERT OR IGNORE INTO loot_entries(loot_entry_id,loot_set_id,item_id,blueprint_id,verification_status)
VALUES ('LOOTENTRY-000001','LOOTSET-000001','ITEM-000001','BP-000001','NEEDS_VERIFICATION');

INSERT OR IGNORE INTO item_relationships(item_relationship_id,source_item_id,relationship_type,target_entity_id,verification_status,created_at)
VALUES ('ITEMREL-000001','ITEM-000001','USED_BY_CREATURE','CREATURE-000001','NEEDS_VERIFICATION',datetime('now'));
