import csv, json, sqlite3, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=[ROOT/'database/schema/core.sql',ROOT/'database/migrations/0002_registry_relationships_spawns.sql',ROOT/'database/migrations/0003_source_registry_import_pipeline.sql',ROOT/'database/migrations/0004_canonical_maps.sql']
class ImportPipelineTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/'test.sqlite'
  con=sqlite3.connect(self.db)
  for p in SCHEMA: con.executescript(p.read_text())
  with (ROOT/'database/reference/id-registry.csv').open(newline='') as f:
   for r in csv.DictReader(f): con.execute('INSERT INTO id_registry VALUES(?,?,?,?,?)',(r['entity_type'],r['id_prefix'],int(r['next_sequence']),int(r['width']),r['description']))
  con.commit(); con.close()
 def tearDown(self): self.tmp.cleanup()
 def stage(self):
  return subprocess.run(['python',str(ROOT/'tools/stage_claims.py'),str(ROOT/'imports/examples/synthetic-creature-claims.csv'),str(ROOT/'imports/examples/synthetic-source.json'),'--db',str(self.db)],capture_output=True,text=True,check=True).stdout.strip()
 def test_migration_tables_exist(self):
  con=sqlite3.connect(self.db); names={r[0] for r in con.execute("select name from sqlite_master where type='table'")}; con.close()
  self.assertTrue({'source_versions','import_batches','import_records','claim_candidates','quarantine_records','promotion_log'}.issubset(names))
 def test_staging_never_creates_canonical_entity(self):
  self.stage(); con=sqlite3.connect(self.db)
  self.assertEqual(0,con.execute("select count(*) from entities where canonical_name='Synthetic Test Creature'").fetchone()[0])
  self.assertEqual(1,con.execute("select count(*) from import_records").fetchone()[0]); con.close()
 def test_unassessed_claim_is_quarantined(self):
  self.stage(); con=sqlite3.connect(self.db)
  self.assertGreaterEqual(con.execute("select count(*) from quarantine_records where reason_code='UNASSESSED_EVIDENCE'").fetchone()[0],1); con.close()
 def test_content_hash_is_recorded(self):
  self.stage(); con=sqlite3.connect(self.db); h=con.execute('select content_hash_sha256 from source_versions').fetchone()[0]; con.close()
  self.assertEqual(64,len(h))
if __name__=='__main__': unittest.main()
