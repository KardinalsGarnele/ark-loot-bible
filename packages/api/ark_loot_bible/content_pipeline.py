from __future__ import annotations
import hashlib,json,uuid
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from .config import ROOT
from .database import connection
ALLOWED={"REGION_COLLECTION","SPAWN_COLLECTION","LOOT_COLLECTION","CAVE_COLLECTION","ARTIFACT_COLLECTION","BOSS_COLLECTION","EXPLORER_NOTE_COLLECTION","RESOURCE_COLLECTION"}
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(p): return f"{p}-{uuid.uuid4().hex[:16].upper()}"
def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def h(v): return hashlib.sha256(canon(v).encode()).hexdigest()
def validate_manifest(d):
 e=[]
 for k in ("manifest_code","content_type","target_entity_type","schema_version","source","facts","components"):
  if k not in d:e.append(f"missing:{k}")
 if d.get("content_type")!="OFFICIAL_MAP_PACKAGE":e.append("content_type:unsupported")
 if d.get("target_entity_type")!="MAP":e.append("target_entity_type:must_be_MAP")
 for k in ("source_id","source_type","title","locator","publisher"):
  if not (d.get("source") or {}).get(k):e.append(f"source.{k}:required")
 for k in ("canonical_name","game_title","map_kind","included_with_base_game","official","release_status","verification_status"):
  if k not in (d.get("facts") or {}):e.append(f"facts.{k}:required")
 seen=set()
 for i,c in enumerate(d.get("components") or []):
  kind=c.get("component_type")
  if kind not in ALLOWED:e.append(f"components[{i}].component_type:unsupported")
  if kind in seen:e.append(f"components[{i}].component_type:duplicate")
  seen.add(kind)
  if c.get("component_status") not in {"EMPTY","PARTIAL","COMPLETE"}:e.append(f"components[{i}].component_status:unsupported")
 return e
def import_map_manifest(path,commit=False,actor="content-importer"):
 path=Path(path); text=path.read_text(encoding="utf-8"); d=json.loads(text); errors=validate_manifest(d); sha=hashlib.sha256(text.encode()).hexdigest(); run=uid("CONTENTRUN")
 count=1+len(d.get("components") or [])
 if errors:return {"run_id":run,"mode":"COMMIT" if commit else "DRY_RUN","status":"FAILED","records_seen":count,"records_valid":0,"records_invalid":1,"errors":errors}
 facts=d["facts"]
 if facts["canonical_name"]!="The Island":return {"run_id":run,"mode":"COMMIT" if commit else "DRY_RUN","status":"FAILED","errors":["stable_id:not_registered_for_map"]}
 if not commit:return {"run_id":run,"mode":"DRY_RUN","status":"VALIDATED","manifest_sha256":sha,"records_seen":count,"records_valid":count,"records_invalid":0,"preview":{"map_id":"MAP-000001","facts":facts,"components":d["components"]}}
 with connection() as con:
  con.execute("BEGIN IMMEDIATE")
  existing=con.execute("SELECT * FROM content_manifests WHERE manifest_sha256=?",(sha,)).fetchone()
  if existing and existing["manifest_status"]=="IMPORTED":con.rollback();return {"run_id":run,"mode":"COMMIT","status":"NO_CHANGES","content_manifest_id":existing["content_manifest_id"],"records_seen":count,"records_valid":count,"records_invalid":0}
  s=d["source"]; t=now()
  con.execute("INSERT INTO sources(source_id,source_type,title,locator,publisher,captured_at,notes) VALUES(?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET title=excluded.title,locator=excluded.locator",(s["source_id"],s["source_type"],s["title"],s["locator"],s["publisher"],t,"Official content package"))
  sv=con.execute("SELECT source_version_id FROM source_versions WHERE source_id=? AND content_hash_sha256=?",(s["source_id"],sha)).fetchone()
  if sv: svid=sv[0]
  else:
   svid=uid("SRCVER"); snap=ROOT/"imports/source-snapshots"/s["source_id"]/f"{sha}.json"; snap.parent.mkdir(parents=True,exist_ok=True); snap.write_text(text,encoding="utf-8")
   con.execute("INSERT INTO source_versions(source_version_id,source_id,version_label,content_hash_sha256,retrieved_at,local_snapshot_path) VALUES(?,?,?,?,?,?)",(svid,s["source_id"],d["schema_version"],sha,t,str(snap.relative_to(ROOT))))
  mid=existing["content_manifest_id"] if existing else uid("MANIFEST")
  if not existing:con.execute("INSERT INTO content_manifests(content_manifest_id,manifest_code,content_type,target_entity_type,source_id,source_version_id,game_version,schema_version,manifest_sha256,manifest_status,created_at,notes) VALUES(?,?,?,?,?,?,?,?,?,'VALIDATED',?,?)",(mid,d["manifest_code"],d["content_type"],d["target_entity_type"],s["source_id"],svid,d.get("game_version"),d["schema_version"],sha,t,"Official map content package"))
  mapid="MAP-000001"
  con.execute("INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,verification_status=excluded.verification_status,updated_at=excluded.updated_at",(mapid,"MAP",facts["canonical_name"],"the-island",facts["verification_status"],t,t))
  con.execute("INSERT INTO maps(map_id,internal_name,release_status,official,game_title,map_kind,included_with_base_game,lifecycle_status) VALUES(?,?,?,?,?,?,?,'ACTIVE') ON CONFLICT(map_id) DO UPDATE SET release_status=excluded.release_status,official=excluded.official,game_title=excluded.game_title,map_kind=excluded.map_kind,included_with_base_game=excluded.included_with_base_game",(mapid,None,facts["release_status"],int(facts["official"]),facts["game_title"],facts["map_kind"],int(facts["included_with_base_game"])))
  con.execute("UPDATE map_scope SET canonical_map_id=?,scope_status='ACTIVE',official_status='VERIFIED' WHERE map_name='The Island'",(mapid,))
  con.execute("INSERT OR IGNORE INTO content_manifest_records VALUES(?,?,?,?,?,?,?,?, 'VALID',NULL,NULL)",(uid("MANREC"),mid,"map","MAP",mapid,facts["canonical_name"],canon(facts),h(facts)))
  ids=[]
  for i,c in enumerate(d["components"],1):
   cid=f"MAPCOMP-{i:06d}";ids.append(cid)
   con.execute("INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,updated_at=excluded.updated_at",(cid,"MAP_COMPONENT",f"The Island — {c['display_name']}",f"the-island-{c['component_type'].lower().replace('_','-')}","NEEDS_VERIFICATION",t,t))
   con.execute("INSERT INTO map_components(map_component_id,map_id,component_type,display_name,component_status,verification_status,source_url,notes) VALUES(?,?,?,?,?,'NEEDS_VERIFICATION',?,?) ON CONFLICT(map_id,component_type) DO UPDATE SET display_name=excluded.display_name,component_status=excluded.component_status",(cid,mapid,c["component_type"],c["display_name"],c["component_status"],s["locator"],"Structural collection only; child records require evidence."))
   con.execute("INSERT OR IGNORE INTO entity_relationships(relationship_id,subject_entity_id,predicate,object_entity_id,verification_status,notes) VALUES(?,?,'CONTAINS_COMPONENT',?,'VERIFIED',?)",(f"REL-MAPCOMP-{i:06d}",mapid,cid,"Structural relationship only"))
   con.execute("INSERT OR IGNORE INTO content_manifest_records VALUES(?,?,?,?,?,?,?,?, 'VALID',NULL,NULL)",(uid("MANREC"),mid,f"component:{c['component_type']}","MAP_COMPONENT",cid,c["display_name"],canon(c),h(c)))
  for field,value in {"canonical_name":facts["canonical_name"],"game_title":facts["game_title"],"map_kind":facts["map_kind"],"included_with_base_game":str(facts["included_with_base_game"]).lower(),"official":str(facts["official"]).lower()}.items():
   evid=uid("EVIDENCE");con.execute("INSERT INTO evidence(evidence_id,entity_id,source_id,field_name,claim_value,verification_status,notes) VALUES(?,?,?,?,?,'VERIFIED',?)",(evid,mapid,s["source_id"],field,value,(d.get("evidence_notes") or {}).get(field)));con.execute("INSERT OR IGNORE INTO field_evidence_links(field_evidence_id,entity_id,field_name,evidence_id,is_current,linked_at) VALUES(?,?,?,?,1,?)",(uid("FIELDEV"),mapid,field,evid,t))
  con.execute("UPDATE content_manifests SET manifest_status='IMPORTED',imported_at=? WHERE content_manifest_id=?",(t,mid));con.execute("INSERT INTO content_import_runs VALUES(?,?,'COMMIT','COMPLETED',?,?,0,?,?,NULL)",(run,mid,count,count,t,t));con.commit()
  return {"run_id":run,"mode":"COMMIT","status":"COMPLETED","content_manifest_id":mid,"map_id":mapid,"component_ids":ids,"records_seen":count,"records_valid":count,"records_invalid":0}
def list_content_manifests():
 with connection() as con:return [dict(r) for r in con.execute("SELECT cm.*,(SELECT COUNT(*) FROM content_manifest_records x WHERE x.content_manifest_id=cm.content_manifest_id) record_count FROM content_manifests cm ORDER BY created_at DESC")]
def get_map_content(map_id):
 with connection() as con:
  m=con.execute("SELECT e.entity_id,e.canonical_name,e.verification_status,m.* FROM maps m JOIN entities e ON e.entity_id=m.map_id WHERE m.map_id=?",(map_id,)).fetchone()
  if not m:return None
  return {"map":dict(m),"components":[dict(r) for r in con.execute("SELECT mc.*,e.canonical_name FROM map_components mc JOIN entities e ON e.entity_id=mc.map_component_id WHERE mc.map_id=? ORDER BY component_type",(map_id,))],"evidence":[dict(r) for r in con.execute("SELECT ev.*,s.title,s.locator FROM evidence ev JOIN sources s ON s.source_id=ev.source_id WHERE ev.entity_id=? ORDER BY field_name",(map_id,))]}
