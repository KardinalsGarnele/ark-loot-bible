#!/usr/bin/env python3
"""Promote one validated import record after evidence checks."""
from __future__ import annotations
import argparse, sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/generated/ark_loot_bible.sqlite'
PREFIX={"MAP":"MAP","CREATURE":"CREATURE","CREATURE_VARIANT":"VARIANT","ITEM":"ITEM","BLUEPRINT":"BP","LOOT_SOURCE":"LSRC","LOOT_SET":"LSET","LOOT_ENTRY":"LENT","BOSS":"BOSS","TEKGRAM":"TEK","ARTIFACT":"ART"}

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def main():
 p=argparse.ArgumentParser(); p.add_argument('import_record_id'); p.add_argument('--db',type=Path,default=DB); p.add_argument('--actor',default='manual-review'); a=p.parse_args()
 con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row; con.execute('PRAGMA foreign_keys=ON')
 try:
  rec=con.execute('SELECT * FROM import_records WHERE import_record_id=?',(a.import_record_id,)).fetchone()
  if not rec: raise SystemExit('Import record not found')
  if rec['record_status']!='VALID': raise SystemExit('Record is not VALID')
  bad=con.execute("SELECT count(*) FROM claim_candidates WHERE import_record_id=? AND candidate_status<>'VALID'",(a.import_record_id,)).fetchone()[0]
  if bad: raise SystemExit('All claims must be VALID before promotion')
  et=rec['entity_type']; prefix=PREFIX[et]
  row=con.execute('SELECT next_sequence,width FROM id_registry WHERE entity_type=?',(et,)).fetchone()
  if not row: raise SystemExit(f'No ID registry for {et}')
  entity_id=rec['proposed_entity_id'] or f"{prefix}-{row['next_sequence']:0{row['width']}d}"
  con.execute('UPDATE id_registry SET next_sequence=next_sequence+1 WHERE entity_type=?',(et,))
  con.execute("INSERT INTO entities(entity_id,entity_type,canonical_name,verification_status,created_at,updated_at) VALUES(?,?,?,?,?,?)",
              (entity_id,et,rec['proposed_canonical_name'],'NEEDS_VERIFICATION',now(),now()))
  con.execute("UPDATE import_records SET proposed_entity_id=?, record_status='PROMOTED' WHERE import_record_id=?",(entity_id,a.import_record_id))
  con.execute("UPDATE claim_candidates SET candidate_status='PROMOTED' WHERE import_record_id=?",(a.import_record_id,))
  pid='PROMO-'+a.import_record_id.split('-',1)[-1]
  con.execute('INSERT INTO promotion_log VALUES(?,?,?,?,?,?)',(pid,a.import_record_id,entity_id,now(),a.actor,'Evidence checks passed; entity remains NEEDS_VERIFICATION until field evidence is attached.'))
  con.commit(); print(entity_id)
 finally: con.close()
if __name__=='__main__': main()
