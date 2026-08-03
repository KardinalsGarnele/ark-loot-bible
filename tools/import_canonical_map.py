#!/usr/bin/env python3
"""Stage and promote a canonical map fixture in one reproducible command."""
import argparse, sqlite3, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('claims',type=Path); p.add_argument('source',type=Path); p.add_argument('--db',type=Path,default=ROOT/'database/generated/ark_loot_bible.sqlite'); p.add_argument('--actor',default='canonical-map-import')
a=p.parse_args()
out=subprocess.check_output([sys.executable,str(ROOT/'tools/stage_claims.py'),str(a.claims),str(a.source),'--db',str(a.db)],text=True).strip()
con=sqlite3.connect(a.db); rec=con.execute('select import_record_id from import_records where import_batch_id=?',(out,)).fetchone()[0]; con.close()
subprocess.run([sys.executable,str(ROOT/'tools/promote_map.py'),rec,'--db',str(a.db),'--actor',a.actor],check=True)
