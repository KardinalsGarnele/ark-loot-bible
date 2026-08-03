import json, sqlite3, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FoundationTests(unittest.TestCase):
 def setUp(self):
  self.con=sqlite3.connect(':memory:')
  self.con.executescript((ROOT/'database/schema/core.sql').read_text())
  self.con.executescript((ROOT/'database/migrations/0002_registry_relationships_spawns.sql').read_text())
 def tearDown(self): self.con.close()
 def test_expected_tables(self):
  names={r[0] for r in self.con.execute("select name from sqlite_master where type='table'")}
  self.assertTrue({'entities','id_registry','entity_relationships','map_scope','spawn_regions','spawn_containers','creature_spawn_entries'}.issubset(names))
 def test_scope_is_noncanonical(self):
  data=json.loads((ROOT/'database/seeds/map-scope.json').read_text())
  self.assertEqual(13,len(data)); self.assertTrue(all(x['official_status']=='NEEDS_VERIFICATION' for x in data))
 def test_reference_graph_ids_unique(self):
  d=json.loads((ROOT/'database/seeds/rex-reference.json').read_text())
  ids=[x['id'] for x in d['entities']]+[x['id'] for x in d['relationships']]
  self.assertEqual(len(ids),len(set(ids)))
if __name__=='__main__': unittest.main()
