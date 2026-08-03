#!/usr/bin/env python3
from pathlib import Path
import csv, sqlite3
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/generated/ark_loot_bible.sqlite'
CSV_PATH=ROOT/'database/reference/id-registry.csv'
def main():
 con=sqlite3.connect(DB)
 try:
  with CSV_PATH.open(encoding='utf-8',newline='') as f:
   for r in csv.DictReader(f):
    con.execute('INSERT OR REPLACE INTO id_registry(entity_type,id_prefix,next_sequence,width,description) VALUES(?,?,?,?,?)',
                (r['entity_type'],r['id_prefix'],int(r['next_sequence']),int(r['width']),r['description']))
  con.commit()
 finally: con.close()
 print('ID registry seeded.')
if __name__=='__main__': main()
