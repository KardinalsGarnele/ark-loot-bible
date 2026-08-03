from __future__ import annotations
from typing import Any
from .database import connection

STATUSES=("VERIFIED","NEEDS_VERIFICATION","REJECTED","DEPRECATED","UNKNOWN")

def _counts(con, table, status_col="verification_status", where="", params=()):
    rows=con.execute(
        f"SELECT COALESCE({status_col},'UNKNOWN') status, COUNT(*) n FROM {table} {where} GROUP BY COALESCE({status_col},'UNKNOWN')",
        params
    ).fetchall()
    data={s:0 for s in STATUSES}
    for r in rows:data[r["status"] if r["status"] in data else "UNKNOWN"]=r["n"]
    data["TOTAL"]=sum(data.values())
    data["VERIFIED_PERCENT"]=round((data["VERIFIED"]/data["TOTAL"]*100),2) if data["TOTAL"] else 0.0
    return data

def global_coverage()->dict[str,Any]:
    with connection() as con:
        sections={
            "maps":_counts(con,"entities",where="WHERE entity_type='MAP'"),
            "creatures":_counts(con,"entities",where="WHERE entity_type='CREATURE'"),
            "items":_counts(con,"entities",where="WHERE entity_type='ITEM'"),
            "blueprints":_counts(con,"entities",where="WHERE entity_type='BLUEPRINT'"),
            "loot_sources":_counts(con,"loot_sources"),
            "loot_sets":_counts(con,"loot_sets"),
            "loot_entries":_counts(con,"loot_entries"),
            "quality_profiles":_counts(con,"quality_profiles"),
        }
        totals={k:sum(v[k] for v in sections.values()) for k in ["VERIFIED","NEEDS_VERIFICATION","REJECTED","DEPRECATED","UNKNOWN","TOTAL"]}
        totals["VERIFIED_PERCENT"]=round(totals["VERIFIED"]/totals["TOTAL"]*100,2) if totals["TOTAL"] else 0.0
        return {"totals":totals,"sections":sections}

def map_coverage(map_id:str)->dict[str,Any]|None:
    with connection() as con:
        maprow=con.execute("""SELECT e.entity_id,e.canonical_name,e.verification_status
          FROM entities e JOIN maps m ON m.map_id=e.entity_id WHERE e.entity_id=?""",(map_id,)).fetchone()
        if not maprow:return None
        groups=[dict(r) for r in con.execute("""SELECT g.source_group,g.group_status,g.verification_status,
          COUNT(DISTINCT l.loot_source_id) loot_sources,COUNT(DISTINCT ls.loot_set_id) loot_sets,
          COUNT(DISTINCT le.loot_entry_id) loot_entries,
          SUM(CASE WHEN le.verification_status='VERIFIED' THEN 1 ELSE 0 END) verified_entries
          FROM map_loot_group_status g
          LEFT JOIN loot_sources l ON l.map_id=g.map_id AND l.source_group=g.source_group
          LEFT JOIN loot_sets ls ON ls.loot_source_id=l.loot_source_id
          LEFT JOIN loot_entries le ON le.loot_set_id=ls.loot_set_id
          WHERE g.map_id=? GROUP BY g.source_group,g.group_status,g.verification_status
          ORDER BY g.source_group""",(map_id,))]
        for g in groups:
            total=g["loot_entries"] or 0
            g["verified_percent"]=round((g["verified_entries"] or 0)/total*100,2) if total else 0.0
        components=[dict(r) for r in con.execute("""SELECT component_type,component_status,verification_status
          FROM map_components WHERE map_id=? ORDER BY component_type""",(map_id,))]
        return {"map":dict(maprow),"loot_groups":groups,"components":components}

def gaps(limit:int=100)->list[dict[str,Any]]:
    with connection() as con:
        rows=con.execute("""SELECT e.entity_id,e.entity_type,e.canonical_name,e.verification_status
          FROM entities e WHERE e.verification_status!='VERIFIED'
          ORDER BY CASE e.verification_status WHEN 'NEEDS_VERIFICATION' THEN 0 ELSE 1 END,
                   e.entity_type,e.canonical_name LIMIT ?""",(limit,)).fetchall()
        return [dict(r) for r in rows]
