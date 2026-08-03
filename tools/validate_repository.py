#!/usr/bin/env python3
from pathlib import Path
import csv, json, sqlite3, subprocess, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]
errors=[]
required=[
 'database/schema/core.sql','database/migrations/0002_registry_relationships_spawns.sql',
 'database/migrations/0003_source_registry_import_pipeline.sql','database/reference/id-registry.csv',
 'database/seeds/map-scope.json','database/seeds/rex-reference.json',
 'docs/data/source-registry.md','docs/data/import-pipeline.md','docs/data/quarantine.md'
]
for rel in required:
 if not (ROOT/rel).exists(): errors.append(f'Missing {rel}')
for rel in ['database/seeds/map-scope.json','database/seeds/rex-reference.json','imports/examples/synthetic-source.json']:
 try: json.loads((ROOT/rel).read_text())
 except Exception as e: errors.append(f'Invalid JSON {rel}: {e}')
try:
 con=sqlite3.connect(':memory:')
 for rel in ['database/schema/core.sql','database/migrations/0002_registry_relationships_spawns.sql','database/migrations/0003_source_registry_import_pipeline.sql']:
  con.executescript((ROOT/rel).read_text())
 with (ROOT/'database/reference/id-registry.csv').open(newline='') as f:
  rows=list(csv.DictReader(f))
  types=[r['entity_type'] for r in rows]; prefixes=[r['id_prefix'] for r in rows]
  if len(types)!=len(set(types)): errors.append('Duplicate entity_type in ID registry')
  if len(prefixes)!=len(set(prefixes)): errors.append('Duplicate id_prefix in ID registry')
  for r in rows: con.execute('INSERT INTO id_registry VALUES(?,?,?,?,?)',(r['entity_type'],r['id_prefix'],int(r['next_sequence']),int(r['width']),r['description']))
 if con.execute('PRAGMA foreign_key_check').fetchall(): errors.append('Foreign key validation failed')
finally:
 try: con.close()
 except: pass
if errors:
 print('\n'.join(errors)); sys.exit(1)
print('Repository validation passed.')
