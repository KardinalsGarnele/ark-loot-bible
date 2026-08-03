from __future__ import annotations
import hashlib,json,uuid
from datetime import datetime,timezone
from pathlib import Path
from .database import connection

ALLOWED={'CLASSIFICATION','BLUEPRINTS','CRAFTING','REPAIR','LOOT','CREATURE_USE','MAP_AVAILABILITY','TECHNICAL'}

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(p): return f"{p}-{uuid.uuid4().hex[:16].upper()}"

def validate(d):
    errors=[]
    if d.get('content_type')!='ITEM_BLUEPRINT_PACKAGE': errors.append('content_type:unsupported')
    for k in ('manifest_code','schema_version','source','item','blueprint','components'):
        if k not in d: errors.append(f'missing:{k}')
    item=d.get('item') or {}
    for k in ('item_id','canonical_name','game_title','item_category','verification_status'):
        if not item.get(k): errors.append(f'item.{k}:required')
    bp=d.get('blueprint') or {}
    for k in ('blueprint_id','canonical_name','blueprint_type','verification_status'):
        if not bp.get(k): errors.append(f'blueprint.{k}:required')
    seen=set()
    for i,c in enumerate(d.get('components') or []):
        t=c.get('component_type')
        if t not in ALLOWED: errors.append(f'components[{i}].component_type:unsupported')
        if t in seen: errors.append(f'components[{i}].component_type:duplicate')
        seen.add(t)
        if c.get('component_status') not in {'EMPTY','PARTIAL','COMPLETE'}:
            errors.append(f'components[{i}].component_status:unsupported')
    return errors

def import_item_manifest(path,commit=False,actor='item-content-importer'):
    path=Path(path); text=path.read_text(encoding='utf-8'); d=json.loads(text)
    errors=validate(d); sha=hashlib.sha256(text.encode()).hexdigest()
    count=2+len(d.get('components') or [])
    if errors:
        return {'mode':'COMMIT' if commit else 'DRY_RUN','status':'FAILED','errors':errors,'records_seen':count}
    if not commit:
        return {'mode':'DRY_RUN','status':'VALIDATED','manifest_sha256':sha,
                'records_seen':count,'records_valid':count,'preview':d}
    with connection() as con:
        con.execute('BEGIN IMMEDIATE')
        old=con.execute('SELECT * FROM item_content_imports WHERE manifest_sha256=?',(sha,)).fetchone()
        if old:
            con.rollback()
            return {'mode':'COMMIT','status':'NO_CHANGES','manifest_sha256':sha,
                    'item_id':old['item_id'],'blueprint_id':old['blueprint_id'],'records_seen':count}
        t=now(); s=d['source']; item=d['item']; bp=d['blueprint']
        con.execute("""INSERT INTO sources(source_id,source_type,title,locator,publisher,captured_at,notes)
          VALUES(?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET
          title=excluded.title,locator=excluded.locator""",
          (s['source_id'],s['source_type'],s['title'],s['locator'],s['publisher'],t,d.get('notes')))
        con.execute("""INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,
          verification_status=excluded.verification_status,updated_at=excluded.updated_at""",
          (item['item_id'],'ITEM',item['canonical_name'],item['canonical_name'].lower().replace(' ','-'),
           item['verification_status'],t,t))
        con.execute("""INSERT INTO items(item_id,item_category,quality_capable,game_title,description,lifecycle_status)
          VALUES(?,?,?,?,?,'ACTIVE') ON CONFLICT(item_id) DO UPDATE SET item_category=excluded.item_category,
          quality_capable=excluded.quality_capable,game_title=excluded.game_title,description=excluded.description""",
          (item['item_id'],item['item_category'],int(bool(item.get('quality_capable'))),
           item['game_title'],d.get('notes')))
        con.execute("""INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,
          verification_status=excluded.verification_status,updated_at=excluded.updated_at""",
          (bp['blueprint_id'],'BLUEPRINT',bp['canonical_name'],bp['canonical_name'].lower().replace(' ','-'),
           bp['verification_status'],t,t))
        con.execute("""INSERT INTO blueprints(blueprint_id,item_id,blueprint_type,can_be_looted,can_be_crafted,
          lifecycle_status,verification_status) VALUES(?,?,?,?,?,'ACTIVE',?)
          ON CONFLICT(blueprint_id) DO UPDATE SET item_id=excluded.item_id,
          blueprint_type=excluded.blueprint_type,can_be_looted=excluded.can_be_looted,
          can_be_crafted=excluded.can_be_crafted,verification_status=excluded.verification_status""",
          (bp['blueprint_id'],item['item_id'],bp['blueprint_type'],bp.get('can_be_looted'),
           bp.get('can_be_crafted'),bp['verification_status']))
        ids=[]
        for i,c in enumerate(d['components'],1):
            cid=f"ITEMCOMP-{i:06d}"; ids.append(cid)
            con.execute("""INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,
              updated_at=excluded.updated_at""",
              (cid,'ITEM_COMPONENT',f"{item['canonical_name']} — {c['display_name']}",
               f"rex-saddle-{c['component_type'].lower().replace('_','-')}",'NEEDS_VERIFICATION',t,t))
            con.execute("""INSERT INTO item_components(item_component_id,item_id,component_type,display_name,
              component_status,verification_status,notes) VALUES(?,?,?,?,?,'NEEDS_VERIFICATION',?)
              ON CONFLICT(item_id,component_type) DO UPDATE SET display_name=excluded.display_name,
              component_status=excluded.component_status""",
              (cid,item['item_id'],c['component_type'],c['display_name'],c['component_status'],
               'Structural collection only; detailed facts require evidence.'))
            con.execute("""INSERT OR IGNORE INTO entity_relationships(relationship_id,subject_entity_id,predicate,
              object_entity_id,verification_status,notes) VALUES(?,?,'CONTAINS_COMPONENT',?,'VERIFIED',?)""",
              (f"REL-ITEMCOMP-{i:06d}",item['item_id'],cid,'Structural relationship only'))
        con.execute("""INSERT OR IGNORE INTO entity_relationships(relationship_id,subject_entity_id,predicate,
          object_entity_id,verification_status,notes) VALUES('REL-ITEM-BP-000001',?,'HAS_BLUEPRINT',?,
          'NEEDS_VERIFICATION',?)""",
          (item['item_id'],bp['blueprint_id'],'Blueprint relationship is structural until source-verified.'))
        con.execute("INSERT INTO item_content_imports VALUES(?,?,?, ?,?,'IMPORTED',?,?)",
          (uid('ITEMIMPORT'),sha,item['item_id'],bp['blueprint_id'],s['source_id'],t,d.get('notes')))
        con.commit()
        return {'mode':'COMMIT','status':'COMPLETED','manifest_sha256':sha,
                'item_id':item['item_id'],'blueprint_id':bp['blueprint_id'],
                'component_ids':ids,'records_seen':count,'records_valid':count}

def get_item_content(item_id):
    with connection() as con:
        item=con.execute("""SELECT e.entity_id,e.canonical_name,e.verification_status,i.*
          FROM items i JOIN entities e ON e.entity_id=i.item_id WHERE i.item_id=?""",(item_id,)).fetchone()
        if not item:return None
        blueprints=[dict(r) for r in con.execute("""SELECT e.canonical_name,e.verification_status,b.*
          FROM blueprints b JOIN entities e ON e.entity_id=b.blueprint_id
          WHERE b.item_id=? ORDER BY e.canonical_name""",(item_id,))]
        components=[dict(r) for r in con.execute("""SELECT e.canonical_name,ic.*
          FROM item_components ic JOIN entities e ON e.entity_id=ic.item_component_id
          WHERE ic.item_id=? ORDER BY ic.component_type""",(item_id,))]
        return {'item':dict(item),'blueprints':blueprints,'components':components}
