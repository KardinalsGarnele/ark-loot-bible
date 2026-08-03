import csv, sqlite3, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'packages/importer'))
from ark_loot_bible_importer import IngestionEngine

class IngestionEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/'test.sqlite'
        con=sqlite3.connect(self.db)
        for p in [ROOT/'database/schema/core.sql', *sorted((ROOT/'database/migrations').glob('*.sql'))]: con.executescript(p.read_text())
        con.execute("INSERT INTO sources(source_id,source_type,title,locator,publisher,captured_at) VALUES('SRC-T','TEST','Test','local:test','Tests',CURRENT_TIMESTAMP)")
        con.execute("INSERT INTO source_versions(source_version_id,source_id,content_hash_sha256,retrieved_at) VALUES('SRCVER-T','SRC-T',?,CURRENT_TIMESTAMP)",('0'*64,))
        con.commit(); con.close()
    def tearDown(self): self.tmp.cleanup()
    def test_dry_run_writes_no_import_records(self):
        result=IngestionEngine(self.db).run(ROOT/'imports/samples/entities.csv','canonical-entity-csv-v1')
        self.assertEqual('COMPLETED',result.status)
        con=sqlite3.connect(self.db); self.assertEqual(0,con.execute('select count(*) from import_records').fetchone()[0]); con.close()
    def test_commit_is_idempotent(self):
        engine=IngestionEngine(self.db); first=engine.run(ROOT/'imports/samples/entities.csv','canonical-entity-csv-v1',commit=True); second=engine.run(ROOT/'imports/samples/entities.csv','canonical-entity-csv-v1',commit=True)
        self.assertEqual('COMPLETED',first.status); self.assertEqual('NO_CHANGES',second.status)
        con=sqlite3.connect(self.db); self.assertEqual(2,con.execute('select count(*) from import_records').fetchone()[0]); con.close()
    def test_invalid_rows_fail_without_partial_records(self):
        bad=Path(self.tmp.name)/'bad.csv'; bad.write_text('entity_type,external_key,canonical_name\nITEM,x,\n',encoding='utf-8')
        with self.assertRaises(ValueError): IngestionEngine(self.db).run(bad,'canonical-entity-csv-v1',commit=True)
        con=sqlite3.connect(self.db); self.assertEqual(0,con.execute('select count(*) from import_records').fetchone()[0]); con.close()
