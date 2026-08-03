import csv, sqlite3, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=[ROOT/'database/schema/core.sql',ROOT/'database/migrations/0002_registry_relationships_spawns.sql',ROOT/'database/migrations/0003_source_registry_import_pipeline.sql',ROOT/'database/migrations/0004_canonical_maps.sql']
class CanonicalMapTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/'x.sqlite'; con=sqlite3.connect(self.db)
  for p in SCHEMA: con.executescript(p.read_text())
  with (ROOT/'database/reference/id-registry.csv').open(newline='') as f:
   for r in csv.DictReader(f): con.execute('insert into id_registry values(?,?,?,?,?)',(r['entity_type'],r['id_prefix'],int(r['next_sequence']),int(r['width']),r['description']))
  con.execute("insert into map_scope(scope_id,map_name) values('SCOPE-MAP-000001','The Island')"); con.commit(); con.close()
 def tearDown(self): self.tmp.cleanup()
 def run_import(self):
  subprocess.run([sys.executable,str(ROOT/'tools/import_canonical_map.py'),str(ROOT/'imports/canonical-maps/the-island-claims.csv'),str(ROOT/'imports/canonical-maps/the-island-source.json'),'--db',str(self.db)],check=True,capture_output=True,text=True)
 def test_promotes_map_and_evidence(self):
  self.run_import(); con=sqlite3.connect(self.db)
  self.assertEqual(('The Island','VERIFIED'),con.execute("select canonical_name,verification_status from entities where entity_id='MAP-000001'").fetchone())
  self.assertEqual(('ARK: Survival Ascended','STORY',1,1),con.execute("select game_title,map_kind,included_with_base_game,official from maps where map_id='MAP-000001'").fetchone())
  self.assertEqual(5,con.execute("select count(*) from evidence where entity_id='MAP-000001'").fetchone()[0])
  self.assertEqual('MAP-000001',con.execute("select canonical_map_id from map_scope where map_name='The Island'").fetchone()[0]); con.close()
 def test_duplicate_promotion_is_rejected(self):
  self.run_import()
  r=subprocess.run([sys.executable,str(ROOT/'tools/import_canonical_map.py'),str(ROOT/'imports/canonical-maps/the-island-claims.csv'),str(ROOT/'imports/canonical-maps/the-island-source.json'),'--db',str(self.db)],capture_output=True,text=True)
  self.assertNotEqual(0,r.returncode)
if __name__=='__main__': unittest.main()
