#!/usr/bin/env python3
"""Stage CSV claims into the import pipeline without promoting canonical data."""
from __future__ import annotations
import argparse, csv, hashlib, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database/generated/ark_loot_bible.sqlite"
ALLOWED_ENTITY_TYPES = {"MAP","CREATURE","CREATURE_VARIANT","ITEM","BLUEPRINT","LOOT_SOURCE","LOOT_SET","LOOT_ENTRY","BOSS","TEKGRAM","ARTIFACT"}
ALLOWED_STRENGTHS = {"PRIMARY","SECONDARY","COMMUNITY","CONFLICTING","UNASSESSED"}

def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("csv_path", type=Path)
    p.add_argument("source_json", type=Path)
    p.add_argument("--db", type=Path, default=DB)
    args=p.parse_args()
    rows=list(csv.DictReader(args.csv_path.open(encoding="utf-8", newline="")))
    src=json.loads(args.source_json.read_text(encoding="utf-8"))
    digest=hashlib.sha256(args.csv_path.read_bytes()).hexdigest()
    con=sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys=ON")
    try:
        con.execute("INSERT OR IGNORE INTO sources(source_id,source_type,title,locator,publisher,captured_at,notes) VALUES(?,?,?,?,?,?,?)",
                    (src['source_id'],src['source_type'],src['title'],src.get('locator'),src.get('publisher'),src.get('captured_at'),src.get('notes')))
        sv=uid("SRCVER")
        con.execute("INSERT INTO source_versions VALUES(?,?,?,?,?,?,?,?)",
                    (sv,src['source_id'],src.get('version_label'),digest,now(),None,None,str(args.csv_path)))
        batch=uid("BATCH")
        con.execute("INSERT INTO import_batches(import_batch_id,source_version_id,importer_name,importer_version,started_at,batch_status,record_count) VALUES(?,?,?,?,?,?,?)",
                    (batch,sv,"stage_claims.py","0.3.0",now(),"STAGED",len({r['source_row_key'] for r in rows})))
        grouped={}
        for r in rows: grouped.setdefault(r['source_row_key'],[]).append(r)
        for key, claims in grouped.items():
            first=claims[0]; errors=[]
            if first['entity_type'] not in ALLOWED_ENTITY_TYPES: errors.append('UNKNOWN_ENTITY_TYPE')
            if not first['proposed_canonical_name'].strip(): errors.append('MISSING_CANONICAL_NAME')
            rec=uid("IREC")
            status="QUARANTINED" if errors else "VALID"
            payload={c['field_name']:c['claim_value'] for c in claims}
            con.execute("INSERT INTO import_records VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (rec,batch,key,first['entity_type'],first.get('proposed_entity_id') or None,first['proposed_canonical_name'],json.dumps(payload,sort_keys=True),status,json.dumps(errors) if errors else None,now()))
            for c in claims:
                strength=c.get('evidence_strength') or 'UNASSESSED'
                candidate_status="VALID" if strength in ALLOWED_STRENGTHS and strength != 'UNASSESSED' else "QUARANTINED"
                cid=uid("CLAIM")
                con.execute("INSERT INTO claim_candidates VALUES(?,?,?,?,?,?,?,?)",
                            (cid,rec,c['field_name'],c['claim_value'],strength,'NEEDS_VERIFICATION',candidate_status,c.get('notes')))
                if candidate_status == "QUARANTINED":
                    qid=uid("QUAR")
                    con.execute("INSERT OR IGNORE INTO quarantine_records VALUES(?,?,?,?,?,?,?)",
                                (qid,rec,'UNASSESSED_EVIDENCE',f"Field {c['field_name']} lacks assessed evidence",now(),None,None))
            if errors:
                qid=uid("QUAR")
                con.execute("INSERT OR IGNORE INTO quarantine_records VALUES(?,?,?,?,?,?,?)",
                            (qid,rec,errors[0],'; '.join(errors),now(),None,None))
        con.execute("UPDATE import_batches SET completed_at=?, batch_status='VALIDATED' WHERE import_batch_id=?",(now(),batch))
        con.commit()
        print(batch)
    finally: con.close()
    return 0
if __name__=='__main__': raise SystemExit(main())
