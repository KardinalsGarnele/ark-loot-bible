INSERT OR IGNORE INTO item_categories(category_code, display_name, parent_category_code, sort_order) VALUES
('RESOURCE', 'Resource', NULL, 10),
('CONSUMABLE', 'Consumable', NULL, 20),
('EQUIPMENT', 'Equipment', NULL, 30),
('SADDLE', 'Saddle', 'EQUIPMENT', 31),
('ARMOR', 'Armor', 'EQUIPMENT', 32),
('WEAPON', 'Weapon', 'EQUIPMENT', 33),
('AMMUNITION', 'Ammunition', 'EQUIPMENT', 34),
('STRUCTURE', 'Structure', NULL, 40),
('TRIBUTE', 'Tribute', NULL, 50),
('ARTIFACT', 'Artifact', NULL, 60),
('TOOL', 'Tool', 'EQUIPMENT', 70),
('MISC', 'Miscellaneous', NULL, 999);
