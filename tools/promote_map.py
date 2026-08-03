#!/usr/bin/env python3
"""Promote one validated MAP import into canonical entity, map, and evidence rows."""
from __future__ import annotations
import argparse, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/generated/ark_loot_bible.sqlite'
POLICY='canonical-map-policy/1.0'
ALLOWED={'canonical_name','game_title','map_kind','included_with_base_game','official','internal_name','release_status'}
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(p): return f'{p}-{uuid.uuid4().hex[:16].upper()}'
def b(v): return 1 if str(v).strip().lower() in {'1','true','yes'} else 0
def main():
 p=argparse.ArgumentParser(); p.add_argument('import_record_id'); p.add_argument('--db',type=Path,default=DB); p.add_argument('--actor',default='map-reviewer'); a=p.parse_args()
 con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row; con.execute('PRAGMA foreign_keys=ON')
 try:
  rec=con.execute('select * from import_records where import_record_id=?',(a.import_record_id,)).fetchone()
  if not rec or rec['entity_type']!='MAP': raise SystemExit('Validated MAP import record required')
  if rec['record_status']!='VALID': raise SystemExit('Record is not VALID')
  claims=con.execute('select * from claim_candidates where import_record_id=?',(a.import_record_id,)).fetchall()
  if not claims or any(c['candidate_status']!='VALID' for c in claims): raise SystemExit('All claims must be VALID')
  data={c['field_name']:c['claim_value'] for c in claims}
  unknown=set(data)-ALLOWED
  if unknown: raise SystemExit(f'Unsupported map fields: {sorted(unknown)}')
  required={'canonical_name','game_title','map_kind','included_with_base_game','official'}
  if not required.issubset(data): raise SystemExit(f'Missing fields: {sorted(required-set(data))}')
  map_id=rec['proposed_entity_id']
  if not map_id or not map_id.startswith('MAP-'): raise SystemExit('A stable proposed MAP id is required')
  if con.execute('select 1 from entities where entity_id=?',(map_id,)).fetchone(): raise SystemExit('Entity already exists')
  t=now()
  con.execute('insert into entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at) values(?,?,?,?,?,?,?)',(map_id,'MAP',data['canonical_name'],data['canonical_name'].lower().replace(' ','-'),'VERIFIED',t,t))
  con.execute('insert into maps(map_id,internal_name,release_status,official,game_title,map_kind,included_with_base_game,lifecycle_status) values(?,?,?,?,?,?,?,?)',(map_id,data.get('internal_name'),data.get('release_status'),b(data['official']),data['game_title'],data['map_kind'],b(data['included_with_base_game']),'ACTIVE'))
  source=con.execute('select s.source_id from import_batches b join source_versions v on v.source_version_id=b.source_version_id join sources s on s.source_id=v.source_id where b.import_batch_id=?',(rec['import_batch_id'],)).fetchone()[0]
  for c in claims:
   eid=uid('EVID'); con.execute('insert into evidence(evidence_id,entity_id,source_id,field_name,claim_value,verification_status,valid_from,notes) values(?,?,?,?,?,?,?,?)',(eid,map_id,source,c['field_name'],c['claim_value'],'VERIFIED',t,c['notes']))
   con.execute('insert into field_evidence_links values(?,?,?,?,?,?)',(uid('FEV'),map_id,c['field_name'],eid,1,t))
  con.execute("update import_records set proposed_entity_id=?,record_status='PROMOTED' where import_record_id=?",(map_id,a.import_record_id))
  con.execute("update claim_candidates set candidate_status='PROMOTED' where import_record_id=?",(a.import_record_id,))
  con.execute('insert into promotion_log values(?,?,?,?,?,?)',(uid('PROMO'),a.import_record_id,map_id,t,a.actor,'Canonical map policy passed.'))
  con.execute('insert into canonical_map_imports values(?,?,?,?,?,?)',(uid('CMI'),a.import_record_id,map_id,POLICY,t,a.actor))
  con.execute("update map_scope set canonical_map_id=?,scope_status='IN_PROGRESS',official_status='VERIFIED' where map_name=?",(map_id,data['canonical_name']))
  con.commit(); print(map_id)
 finally: con.close()
if __name__=='__main__': main()
