-- Development-only reference graph. These records are intentionally not VERIFIED.
INSERT OR IGNORE INTO entities(entity_id, entity_type, canonical_name, slug, verification_status, created_at, updated_at)
VALUES ('CREATURE-000001','CREATURE','Rex','rex','NEEDS_VERIFICATION',datetime('now'),datetime('now'));
INSERT OR IGNORE INTO creatures(creature_id, species_name, tameable, breedable, game_title, internal_name, description, diet_type, temperament)
VALUES ('CREATURE-000001',NULL,NULL,NULL,'ARK: Survival Ascended',NULL,'Development reference record; gameplay facts require evidence.',NULL,NULL);
INSERT OR IGNORE INTO entities(entity_id, entity_type, canonical_name, slug, verification_status, created_at, updated_at)
VALUES ('VARIANT-000001','CREATURE_VARIANT','Rex (Base)','rex-base','NEEDS_VERIFICATION',datetime('now'),datetime('now'));
INSERT OR IGNORE INTO creature_variants(variant_id, creature_id, variant_type, internal_name, is_default)
VALUES ('VARIANT-000001','CREATURE-000001','BASE',NULL,1);
