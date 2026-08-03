from __future__ import annotations
import hashlib,json,uuid
from datetime import datetime,timezone
from pathlib import Path
from .database import connection
ALLOWED={'VARIANTS','MAP_PRESENCE','SPAWNS','TAMING','BREEDING','STATS','DROPS','HARVEST','SADDLE','DOSSIER'}
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(p): return f"{p}-{uuid.uuid4().hex[:16].upper()}"
def validate(d):
 e=[]
 if d.get('content_type')!='CREATURE_PACKAGE': e.append('content_type:unsupported')
 for k in ('manifest_code','schema_version','source','facts','default_variant','components'):
  if k not in d:e.append(f'missing:{k}')
 f=d.get('facts') or {}
 for k in ('creature_id','canonical_name','game_title','verification_status'):
  if not f.get(k):e.append(f'facts.{k}:required')
 v=d.get('default_variant') or {}
 for k in ('variant_id','canonical_name','variant_type','verification_status'):
  if not v.get(k):e.append(f'default_variant.{k}:required')
 seen=set()
 for i,c in enumerate(d.get('components') or []):
  t=c.get('component_type')
  if t not in ALLOWED:e.append(f'components[{i}].component_type:unsupported')
  if t in seen:e.append(f'components[{i}].component_type:duplicate')
  seen.add(t)
  if c.get('component_status') not in {'EMPTY','PARTIAL','COMPLETE'}:e.append(f'components[{i}].component_status:unsupported')
 return e
def import_creature_manifest(path,commit=False,actor='creature-content-importer'):
 path=Path(path); text=path.read_text(encoding='utf-8'); d=json.loads(text); errors=validate(d); sha=hashlib.sha256(text.encode()).hexdigest(); count=2+len(d.get('components') or [])
 if errors:return {'mode':'COMMIT' if commit else 'DRY_RUN','status':'FAILED','errors':errors,'records_seen':count}
 if not commit:return {'mode':'DRY_RUN','status':'VALIDATED','manifest_sha256':sha,'records_seen':count,'records_valid':count,'preview':d}
 with connection() as con:
  con.execute('BEGIN IMMEDIATE')
  old=con.execute('SELECT * FROM creature_content_imports WHERE manifest_sha256=?',(sha,)).fetchone()
  if old: con.rollback(); return {'mode':'COMMIT','status':'NO_CHANGES','manifest_sha256':sha,'creature_id':old['creature_id'],'records_seen':count}
  t=now(); s=d['source']; f=d['facts']; v=d['default_variant']
  con.execute("INSERT INTO sources(source_id,source_type,title,locator,publisher,captured_at,notes) VALUES(?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET title=excluded.title,locator=excluded.locator",(s['source_id'],s['source_type'],s['title'],s['locator'],s['publisher'],t,d.get('notes')))
  con.execute("INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,verification_status=excluded.verification_status,updated_at=excluded.updated_at",(f['creature_id'],'CREATURE',f['canonical_name'],f['canonical_name'].lower().replace(' ','-'),f['verification_status'],t,t))
  con.execute("INSERT INTO creatures(creature_id,game_title,description,lifecycle_status) VALUES(?,?,?,'ACTIVE') ON CONFLICT(creature_id) DO UPDATE SET game_title=excluded.game_title,description=excluded.description",(f['creature_id'],f['game_title'],d.get('notes')))
  con.execute("INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,verification_status=excluded.verification_status,updated_at=excluded.updated_at",(v['variant_id'],'CREATURE_VARIANT',v['canonical_name'],v['canonical_name'].lower().replace(' ','-').replace('(','').replace(')',''),v['verification_status'],t,t))
  con.execute("INSERT INTO creature_variants(variant_id,creature_id,variant_type,is_default,lifecycle_status) VALUES(?,?,?,1,'ACTIVE') ON CONFLICT(variant_id) DO UPDATE SET variant_type=excluded.variant_type,is_default=1",(v['variant_id'],f['creature_id'],v['variant_type']))
  ids=[]
  for i,c in enumerate(d['components'],1):
   cid=f"CRECOMP-{i:06d}"; ids.append(cid)
   con.execute("INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,updated_at=excluded.updated_at",(cid,'CREATURE_COMPONENT',f"{f['canonical_name']} — {c['display_name']}",f"rex-{c['component_type'].lower().replace('_','-')}",'NEEDS_VERIFICATION',t,t))
   con.execute("INSERT INTO creature_components(creature_component_id,creature_id,component_type,display_name,component_status,verification_status,notes) VALUES(?,?,?,?,?,'NEEDS_VERIFICATION',?) ON CONFLICT(creature_id,component_type) DO UPDATE SET display_name=excluded.display_name,component_status=excluded.component_status",(cid,f['creature_id'],c['component_type'],c['display_name'],c['component_status'],'Structural collection only; child facts require evidence.'))
   con.execute("INSERT OR IGNORE INTO entity_relationships(relationship_id,subject_entity_id,predicate,object_entity_id,verification_status,notes) VALUES(?,?,'CONTAINS_COMPONENT',?,'VERIFIED',?)",(f"REL-CRECOMP-{i:06d}",f['creature_id'],cid,'Structural relationship only'))
  con.execute("INSERT INTO creature_content_imports VALUES(?,?,?,?,'IMPORTED',?,?)",(uid('CREIMPORT'),sha,f['creature_id'],s['source_id'],t,d.get('notes')))
  con.commit(); return {'mode':'COMMIT','status':'COMPLETED','manifest_sha256':sha,'creature_id':f['creature_id'],'variant_id':v['variant_id'],'component_ids':ids,'records_seen':count,'records_valid':count}
def get_creature_content(creature_id):
 with connection() as con:
  c=con.execute("SELECT e.entity_id,e.canonical_name,e.verification_status,c.* FROM creatures c JOIN entities e ON e.entity_id=c.creature_id WHERE c.creature_id=?",(creature_id,)).fetchone()
  if not c:return None
  return {'creature':dict(c),'variants':[dict(r) for r in con.execute("SELECT e.canonical_name,e.verification_status,v.* FROM creature_variants v JOIN entities e ON e.entity_id=v.variant_id WHERE v.creature_id=? ORDER BY v.is_default DESC,e.canonical_name",(creature_id,))],'components':[dict(r) for r in con.execute("SELECT e.canonical_name,cc.* FROM creature_components cc JOIN entities e ON e.entity_id=cc.creature_component_id WHERE cc.creature_id=? ORDER BY cc.component_type",(creature_id,))]}
