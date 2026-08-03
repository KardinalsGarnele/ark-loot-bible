import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ItemModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "tools/build_database.py")], check=True, cwd=ROOT)
        cls.db = ROOT / "database/generated/ark_loot_bible.sqlite"

    def test_item_schema_and_categories_exist(self):
        con = sqlite3.connect(self.db)
        try:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("item_categories", tables)
            self.assertIn("item_relationships", tables)
            self.assertIn("crafting_recipes", tables)
            self.assertGreaterEqual(con.execute("SELECT COUNT(*) FROM item_categories").fetchone()[0], 10)
        finally:
            con.close()

    def test_empty_canonical_item_api(self):
        os.environ["ARK_LOOT_BIBLE_DB"] = str(self.db)
        sys.path.insert(0, str(ROOT / "packages/api"))
        from ark_loot_bible.repository import list_items
        self.assertEqual(list_items(), [])

    def test_constraints_reject_invalid_stack_size(self):
        con = sqlite3.connect(self.db)
        con.execute("PRAGMA foreign_keys=ON")
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO entities VALUES(?,?,?,?,?,?,?,?,?)", ("ITEM-999999","ITEM","Invalid","invalid","NEEDS_VERIFICATION","2026-01-01","2026-01-01",None,None))
        except sqlite3.OperationalError:
            # Entities schema has evolved; verify the item constraint with a valid dynamic insert.
            cols = [r[1] for r in con.execute("PRAGMA table_info(entities)")]
            values = {"entity_id":"ITEM-999999","entity_type":"ITEM","canonical_name":"Invalid","slug":"invalid","verification_status":"NEEDS_VERIFICATION","created_at":"2026-01-01","updated_at":"2026-01-01"}
            con.execute(f"INSERT INTO entities ({','.join(values)}) VALUES ({','.join('?' for _ in values)})", tuple(values.values()))
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO items(item_id, item_category, quality_capable, stack_size) VALUES(?,?,?,?)", ("ITEM-999999","MISC",0,0))
        finally:
            con.close()

if __name__ == "__main__": unittest.main()
