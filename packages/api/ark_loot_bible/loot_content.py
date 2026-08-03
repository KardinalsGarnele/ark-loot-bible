from __future__ import annotations
import hashlib,json,uuid
from datetime import datetime,timezone
from pathlib import Path
from .database import connection

COMPONENTS={'IDENTITY','QUALITY_PROFILE','RESPAWN','LOOT_SETS','LOOT_ENTRIES','MAP_RELATION','COORDINATES','TECHNICAL'}

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(p): return f"{p}-{uuid.uuid4().hex[:16].upper()}"

def validate(d):
    errors=[]
    if d.get('content_type')!='LOOT_SOURCE_PACKAGE': errors.append('content_type:unsupported')
    for k in ('manifest_code','schema_version','source','loot_source','loot_sets','components'):
        if k not in d: errors.append(f'missing:{k}')
    ls=d.get('loot_source') or {}
    for k in ('loot_source_id','canonical_name','map_id','source_type','verification_status'):
        if not ls.get(k): errors.append(f'loot_source.{k}:required')
    seen=set()
    for i,c in enumerate(d.get('components') or []):
        t=c.get('component_type')
        if t not in COMPONENTS: errors.append(f'components[{i}].component_type:unsupported')
        if t in seen: errors.append(f'components[{i}].component_type:duplicate')
        seen.add(t)
    for si,s in enumerate(d.get('loot_sets') or []):
        for k in ('loot_set_id','canonical_name','verification_status','entries'):
            if k not in s: errors.append(f'loot_sets[{si}].{k}:required')
        for ei,e in enumerate(s.get('entries') or []):
            for k in ('loot_entry_id','canonical_name','verification_status'):
                if k not in e: errors.append(f'loot_sets[{si}].entries[{ei}].{k}:required')
            if not e.get('item_id') and not e.get('blueprint_id'):
                errors.append(f'loot_sets[{si}].entries[{ei}]:reward_required')
            for key in ('blueprint_chance',):
                v=e.get(key)
                if v is not None and not 0 <= v <= 1: errors.append(f'loot_sets[{si}].entries[{ei}].{key}:range')
    return errors

def import_loot_manifest(path,commit=False,actor='loot-content-importer'):
    path=Path(path); text=path.read_text(encoding='utf-8'); d=json.loads(text)
    errors=validate(d); sha=hashlib.sha256(text.encode()).hexdigest()
    total=1+len(d.get('components') or [])+len(d.get('loot_sets') or [])+sum(len(x.get('entries') or []) for x in d.get('loot_sets') or [])
    if errors:return {'mode':'COMMIT' if commit else 'DRY_RUN','status':'FAILED','errors':errors,'records_seen':total}
    if not commit:return {'mode':'DRY_RUN','status':'VALIDATED','manifest_sha256':sha,'records_seen':total,'records_valid':total,'preview':d}
    with connection() as con:
        con.execute('BEGIN IMMEDIATE')
        old=con.execute('SELECT * FROM loot_content_imports WHERE manifest_sha256=?',(sha,)).fetchone()
        if old:
            con.rollback()
            return {'mode':'COMMIT','status':'NO_CHANGES','manifest_sha256':sha,'loot_source_id':old['loot_source_id'],'records_seen':total}
        t=now(); src=d['source']; ls=d['loot_source']
        for entity_id,table in ((ls['map_id'],'maps'),):
            if not con.execute(f'SELECT 1 FROM {table} WHERE map_id=?',(entity_id,)).fetchone():
                con.rollback(); return {'mode':'COMMIT','status':'FAILED','errors':[f'{table}:{entity_id}:missing'],'records_seen':total}
        con.execute("""INSERT INTO sources(source_id,source_type,title,locator,publisher,captured_at,notes)
          VALUES(?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET title=excluded.title,locator=excluded.locator""",
          (src['source_id'],src['source_type'],src['title'],src['locator'],src['publisher'],t,d.get('notes')))
        con.execute("""INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,
          verification_status=excluded.verification_status,updated_at=excluded.updated_at""",
          (ls['loot_source_id'],'LOOT_SOURCE',ls['canonical_name'],ls['canonical_name'].lower().replace(' ','-'),ls['verification_status'],t,t))
        con.execute("""INSERT INTO loot_sources(loot_source_id,map_id,source_type,description,lifecycle_status,verification_status)
          VALUES(?,?,?,?, 'ACTIVE',?) ON CONFLICT(loot_source_id) DO UPDATE SET map_id=excluded.map_id,
          source_type=excluded.source_type,description=excluded.description,verification_status=excluded.verification_status""",
          (ls['loot_source_id'],ls['map_id'],ls['source_type'],d.get('notes'),ls['verification_status']))
        component_ids=[]
        for i,c in enumerate(d['components'],1):
            cid=f"LOOTCOMP-{i:06d}"; component_ids.append(cid)
            con.execute("""INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,updated_at=excluded.updated_at""",
              (cid,'LOOT_COMPONENT',f"{ls['canonical_name']} — {c['display_name']}",f"loot-{c['component_type'].lower().replace('_','-')}",'NEEDS_VERIFICATION',t,t))
            con.execute("""INSERT INTO loot_content_components VALUES(?,?,?,?,?,'NEEDS_VERIFICATION',?)
              ON CONFLICT(loot_source_id,component_type) DO UPDATE SET display_name=excluded.display_name,component_status=excluded.component_status""",
              (cid,ls['loot_source_id'],c['component_type'],c['display_name'],c['component_status'],'Structural collection only.'))
        set_ids=[]; entry_ids=[]
        for s in d['loot_sets']:
            sid=s['loot_set_id']; set_ids.append(sid)
            con.execute("""INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,updated_at=excluded.updated_at""",
              (sid,'LOOT_SET',s['canonical_name'],s['canonical_name'].lower().replace(' ','-'),s['verification_status'],t,t))
            con.execute("""INSERT INTO loot_sets(loot_set_id,loot_source_id,selection_weight,min_rolls,max_rolls,verification_status)
              VALUES(?,?,?,?,?,?) ON CONFLICT(loot_set_id) DO UPDATE SET loot_source_id=excluded.loot_source_id,
              selection_weight=excluded.selection_weight,min_rolls=excluded.min_rolls,max_rolls=excluded.max_rolls,
              verification_status=excluded.verification_status""",
              (sid,ls['loot_source_id'],s.get('selection_weight'),s.get('min_rolls'),s.get('max_rolls'),s['verification_status']))
            for e in s['entries']:
                eid=e['loot_entry_id']; entry_ids.append(eid)
                if e.get('item_id') and not con.execute('SELECT 1 FROM items WHERE item_id=?',(e['item_id'],)).fetchone():
                    raise ValueError(f"missing item {e['item_id']}")
                if e.get('blueprint_id') and not con.execute('SELECT 1 FROM blueprints WHERE blueprint_id=?',(e['blueprint_id'],)).fetchone():
                    raise ValueError(f"missing blueprint {e['blueprint_id']}")
                con.execute("""INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at)
                  VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET canonical_name=excluded.canonical_name,updated_at=excluded.updated_at""",
                  (eid,'LOOT_ENTRY',e['canonical_name'],e['canonical_name'].lower().replace(' ','-'),e['verification_status'],t,t))
                con.execute("""INSERT INTO loot_entries(loot_entry_id,loot_set_id,item_id,blueprint_id,effective_quality_min,
                  effective_quality_max,entry_weight,min_quantity,max_quantity,blueprint_chance,verification_status)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(loot_entry_id) DO UPDATE SET loot_set_id=excluded.loot_set_id,
                  item_id=excluded.item_id,blueprint_id=excluded.blueprint_id,effective_quality_min=excluded.effective_quality_min,
                  effective_quality_max=excluded.effective_quality_max,entry_weight=excluded.entry_weight,
                  min_quantity=excluded.min_quantity,max_quantity=excluded.max_quantity,
                  blueprint_chance=excluded.blueprint_chance,verification_status=excluded.verification_status""",
                  (eid,sid,e.get('item_id'),e.get('blueprint_id'),e.get('effective_quality_min'),e.get('effective_quality_max'),
                   e.get('entry_weight'),e.get('min_quantity'),e.get('max_quantity'),e.get('blueprint_chance'),e['verification_status']))
        con.execute("INSERT INTO loot_content_imports VALUES(?,?,?,?,'IMPORTED',?,?)",
          (uid('LOOTIMPORT'),sha,ls['loot_source_id'],src['source_id'],t,d.get('notes')))
        con.commit()
        return {'mode':'COMMIT','status':'COMPLETED','manifest_sha256':sha,'loot_source_id':ls['loot_source_id'],
          'loot_set_ids':set_ids,'loot_entry_ids':entry_ids,'component_ids':component_ids,'records_seen':total,'records_valid':total}

def get_loot_content(loot_source_id):
    with connection() as con:
        source=con.execute("""SELECT e.canonical_name,e.verification_status,l.* FROM loot_sources l
          JOIN entities e ON e.entity_id=l.loot_source_id WHERE l.loot_source_id=?""",(loot_source_id,)).fetchone()
        if not source:return None
        comps=[dict(r) for r in con.execute("""SELECT e.canonical_name,c.* FROM loot_content_components c
          JOIN entities e ON e.entity_id=c.loot_content_component_id WHERE c.loot_source_id=? ORDER BY c.component_type""",(loot_source_id,))]
        sets=[]
        for s in con.execute("""SELECT e.canonical_name,s.* FROM loot_sets s JOIN entities e ON e.entity_id=s.loot_set_id
          WHERE s.loot_source_id=? ORDER BY e.canonical_name""",(loot_source_id,)):
            x=dict(s); x['entries']=[dict(r) for r in con.execute("""SELECT e.canonical_name,le.* FROM loot_entries le
              JOIN entities e ON e.entity_id=le.loot_entry_id WHERE le.loot_set_id=? ORDER BY e.canonical_name""",(s['loot_set_id'],))]
            sets.append(x)
        return {'loot_source':dict(source),'components':comps,'sets':sets}
