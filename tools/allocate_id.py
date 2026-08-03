#!/usr/bin/env python3
"""Allocate the next stable entity ID from a SQLite registry."""
import argparse, sqlite3

def allocate(db_path: str, entity_type: str) -> str:
    con=sqlite3.connect(db_path)
    try:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT id_prefix,next_sequence,width FROM id_registry WHERE entity_type=?',(entity_type,)).fetchone()
        if not row: raise ValueError(f'Unknown entity type: {entity_type}')
        prefix, seq, width=row
        entity_id=f'{prefix}-{seq:0{width}d}'
        con.execute('UPDATE id_registry SET next_sequence=? WHERE entity_type=?',(seq+1,entity_type))
        con.commit(); return entity_id
    except Exception:
        con.rollback(); raise
    finally: con.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('database'); p.add_argument('entity_type')
    a=p.parse_args(); print(allocate(a.database,a.entity_type))
