from typing import Any
from .database import connection

ITEM_SELECT = """
SELECT e.entity_id AS item_id, e.canonical_name, e.slug, e.verification_status,
       i.game_title, i.internal_name, i.description, i.stack_size, i.weight,
       i.quality_capable, i.lifecycle_status,
       c.category_code, c.display_name AS category_name
FROM entities e
JOIN items i ON i.item_id = e.entity_id
LEFT JOIN item_category_assignments a ON a.item_id = i.item_id AND a.is_primary = 1
LEFT JOIN item_categories c ON c.category_code = a.category_code
"""

def list_items(q: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    sql = ITEM_SELECT
    params: list[Any] = []
    sql += " WHERE e.verification_status = 'VERIFIED'"
    if q:
        sql += " AND (lower(e.canonical_name) LIKE ? OR lower(e.slug) LIKE ?)"
        needle = f"%{q.lower()}%"
        params.extend([needle, needle])
    sql += " ORDER BY e.canonical_name LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with connection() as con:
        return [dict(row) for row in con.execute(sql, params)]

def get_item(item_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row = con.execute(ITEM_SELECT + " WHERE e.entity_id = ?", (item_id,)).fetchone()
        if not row:
            return None
        item = dict(row)
        item["relationships"] = [dict(r) for r in con.execute(
            """SELECT item_relationship_id, relationship_type, target_entity_id,
                      verification_status, valid_from, valid_to
               FROM item_relationships WHERE source_item_id = ? ORDER BY relationship_type""",
            (item_id,),
        )]
        return item

CREATURE_SELECT = """
SELECT e.entity_id AS creature_id, e.canonical_name, e.slug, e.verification_status,
       c.game_title, c.internal_name, c.description, c.species_name,
       c.tameable, c.breedable, c.diet_type, c.temperament, c.lifecycle_status
FROM entities e
JOIN creatures c ON c.creature_id = e.entity_id
"""

def list_creatures(q: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    sql = CREATURE_SELECT
    params: list[Any] = []
    if q:
        sql += " WHERE lower(e.canonical_name) LIKE ? OR lower(e.slug) LIKE ?"
        needle = f"%{q.lower()}%"
        params.extend([needle, needle])
    sql += " ORDER BY e.canonical_name LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with connection() as con:
        return [dict(row) for row in con.execute(sql, params)]

def get_creature(creature_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row = con.execute(CREATURE_SELECT + " WHERE e.entity_id = ?", (creature_id,)).fetchone()
        if not row:
            return None
        creature = dict(row)
        creature["variants"] = [dict(r) for r in con.execute(
            """SELECT v.variant_id, e.canonical_name, e.slug, v.variant_type,
                      v.internal_name, v.is_default, v.lifecycle_status,
                      e.verification_status
               FROM creature_variants v JOIN entities e ON e.entity_id=v.variant_id
               WHERE v.creature_id=? ORDER BY v.is_default DESC, e.canonical_name""", (creature_id,))]
        creature["maps"] = [dict(r) for r in con.execute(
            """SELECT p.map_id, e.canonical_name, p.presence_type, p.verification_status,
                      p.valid_from, p.valid_to
               FROM creature_map_presence p JOIN entities e ON e.entity_id=p.map_id
               WHERE p.creature_id=? ORDER BY e.canonical_name""", (creature_id,))]
        creature["relationships"] = [dict(r) for r in con.execute(
            """SELECT creature_relationship_id, relationship_type, target_entity_id,
                      verification_status, valid_from, valid_to
               FROM creature_relationships WHERE source_creature_id=? ORDER BY relationship_type""", (creature_id,))]
        return creature

LOOT_SOURCE_SELECT = """
SELECT e.entity_id AS loot_source_id, e.canonical_name, e.slug,
       l.source_type, l.map_id, me.canonical_name AS map_name,
       l.description, l.lifecycle_status, l.verification_status
FROM entities e
JOIN loot_sources l ON l.loot_source_id=e.entity_id
LEFT JOIN entities me ON me.entity_id=l.map_id
"""

def list_loot_sources(q: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    sql = LOOT_SOURCE_SELECT
    params: list[Any] = []
    sql += " WHERE l.verification_status = 'VERIFIED'"
    if q:
        sql += " AND (lower(e.canonical_name) LIKE ? OR lower(e.slug) LIKE ?)"
        needle=f"%{q.lower()}%"; params.extend([needle,needle])
    sql += " ORDER BY e.canonical_name LIMIT ? OFFSET ?"; params.extend([limit,offset])
    with connection() as con:
        return [dict(r) for r in con.execute(sql,params)]

def get_loot_source(loot_source_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row=con.execute(LOOT_SOURCE_SELECT+" WHERE e.entity_id=?",(loot_source_id,)).fetchone()
        if not row: return None
        result=dict(row); result["sets"]=[]
        sets=con.execute("""SELECT s.loot_set_id,e.canonical_name,s.selection_weight,s.min_rolls,s.max_rolls,s.verification_status
                            FROM loot_sets s JOIN entities e ON e.entity_id=s.loot_set_id
                            WHERE s.loot_source_id=? ORDER BY e.canonical_name""",(loot_source_id,)).fetchall()
        for sr in sets:
            sd=dict(sr)
            sd["entries"]=[dict(r) for r in con.execute("""SELECT le.loot_entry_id,ee.canonical_name,le.item_id,ie.canonical_name item_name,
                    le.blueprint_id,be.canonical_name blueprint_name,le.entry_weight,le.min_quantity,le.max_quantity,
                    le.blueprint_chance,le.effective_quality_min,le.effective_quality_max,le.verification_status
                    FROM loot_entries le JOIN entities ee ON ee.entity_id=le.loot_entry_id
                    LEFT JOIN entities ie ON ie.entity_id=le.item_id LEFT JOIN entities be ON be.entity_id=le.blueprint_id
                    WHERE le.loot_set_id=? ORDER BY ee.canonical_name""",(sd["loot_set_id"],))]
            result["sets"].append(sd)
        return result

def get_item_loot_paths(item_id: str) -> list[dict[str, Any]]:
    with connection() as con:
        return [dict(r) for r in con.execute("""SELECT i.item_id,ie.canonical_name item_name,le.blueprint_id,be.canonical_name blueprint_name,
            le.loot_entry_id,ls.loot_set_id,lse.canonical_name loot_set_name,src.loot_source_id,
            se.canonical_name loot_source_name,src.source_type,le.verification_status
            FROM items i JOIN entities ie ON ie.entity_id=i.item_id
            JOIN loot_entries le ON le.item_id=i.item_id
            LEFT JOIN entities be ON be.entity_id=le.blueprint_id
            JOIN loot_sets ls ON ls.loot_set_id=le.loot_set_id JOIN entities lse ON lse.entity_id=ls.loot_set_id
            JOIN loot_sources src ON src.loot_source_id=ls.loot_source_id JOIN entities se ON se.entity_id=src.loot_source_id
            WHERE i.item_id=? ORDER BY se.canonical_name,lse.canonical_name""",(item_id,))]

def global_search(q: str, limit: int = 25, include_unverified: bool = False) -> list[dict[str, Any]]:
    needle = f"%{q.strip().lower()}%"
    prefix = f"{q.strip().lower()}%"
    where = "(lower(canonical_name) LIKE ? OR lower(COALESCE(slug,'')) LIKE ? OR lower(entity_id) LIKE ?)"
    params: list[Any] = [needle, needle, needle]
    if not include_unverified:
        where += " AND verification_status = 'VERIFIED'"
    sql = f"""SELECT entity_id, entity_type, canonical_name, slug, verification_status,
        CASE WHEN lower(canonical_name)=? THEN 100
             WHEN lower(canonical_name) LIKE ? THEN 80
             WHEN lower(COALESCE(slug,'')) LIKE ? THEN 70 ELSE 40 END AS score
        FROM entities WHERE {where}
        ORDER BY score DESC, canonical_name LIMIT ?"""
    params = [q.strip().lower(), prefix, prefix] + params + [limit]
    route = {
        'ITEM': 'items', 'CREATURE': 'creatures', 'LOOT_SOURCE': 'loot-sources',
        'MAP': 'maps', 'BLUEPRINT': 'graph', 'CREATURE_VARIANT': 'graph',
        'LOOT_SET': 'graph', 'LOOT_ENTRY': 'graph'
    }
    with connection() as con:
        rows=[]
        for r in con.execute(sql, params):
            d=dict(r); d['path']=f"/api/v1/{route.get(d['entity_type'],'graph')}/{d['entity_id']}"; rows.append(d)
        return rows

def _node(con, entity_id: str) -> dict[str, Any] | None:
    row=con.execute("SELECT entity_id,entity_type,canonical_name,slug,verification_status FROM entities WHERE entity_id=?",(entity_id,)).fetchone()
    return dict(row) if row else None

def get_entity_graph(entity_id: str, depth: int = 1) -> dict[str, Any] | None:
    with connection() as con:
        root=_node(con,entity_id)
        if not root: return None
        nodes={entity_id:root}; edges=[]; frontier={entity_id}; seen_edges=set()
        def add_edge(edge_type, source_id, target_id, status, table):
            key=(edge_type,source_id,target_id,table)
            if key in seen_edges: return
            seen_edges.add(key); edges.append({'edge_type':edge_type,'source_id':source_id,'target_id':target_id,'verification_status':status,'source_table':table})
            for eid in (source_id,target_id):
                if eid not in nodes:
                    n=_node(con,eid)
                    if n: nodes[eid]=n
        for _ in range(depth):
            current=set(frontier); frontier=set()
            for eid in current:
                queries=[
                  ("SELECT relationship_type,source_entity_id,target_entity_id,verification_status FROM entity_relationships WHERE source_entity_id=? OR target_entity_id=?",'entity_relationships'),
                  ("SELECT relationship_type,source_item_id,target_entity_id,verification_status FROM item_relationships WHERE source_item_id=? OR target_entity_id=?",'item_relationships'),
                  ("SELECT relationship_type,source_creature_id,target_entity_id,verification_status FROM creature_relationships WHERE source_creature_id=? OR target_entity_id=?",'creature_relationships')]
                for sql,table in queries:
                    try:
                        for r in con.execute(sql,(eid,eid)):
                            vals=list(r); add_edge(vals[0],vals[1],vals[2],vals[3],table)
                    except Exception:
                        pass
                for r in con.execute("SELECT blueprint_id,item_id,verification_status FROM blueprints WHERE blueprint_id=? OR item_id=?",(eid,eid)):
                    add_edge('BLUEPRINT_OF',r['blueprint_id'],r['item_id'],r['verification_status'],'blueprints')
                for r in con.execute("SELECT loot_set_id,loot_source_id,verification_status FROM loot_sets WHERE loot_set_id=? OR loot_source_id=?",(eid,eid)):
                    add_edge('CONTAINS_LOOT_SET',r['loot_source_id'],r['loot_set_id'],r['verification_status'],'loot_sets')
                for r in con.execute("SELECT loot_entry_id,loot_set_id,item_id,blueprint_id,verification_status FROM loot_entries WHERE loot_entry_id=? OR loot_set_id=? OR item_id=? OR blueprint_id=?",(eid,eid,eid,eid)):
                    add_edge('CONTAINS_LOOT_ENTRY',r['loot_set_id'],r['loot_entry_id'],r['verification_status'],'loot_entries')
                    if r['item_id']: add_edge('REWARDS_ITEM',r['loot_entry_id'],r['item_id'],r['verification_status'],'loot_entries')
                    if r['blueprint_id']: add_edge('REWARDS_BLUEPRINT',r['loot_entry_id'],r['blueprint_id'],r['verification_status'],'loot_entries')
            for e in edges:
                for candidate in (e['source_id'],e['target_id']):
                    if candidate not in current: frontier.add(candidate)
        return {'root':root,'nodes':sorted(nodes.values(),key=lambda n:n['entity_id']),'edges':edges}

def get_entity_profile(entity_id: str, depth: int = 1) -> dict[str, Any] | None:
    graph = get_entity_graph(entity_id, depth=depth)
    if graph is None:
        return None
    root = graph['root']
    details: dict[str, Any] = {}
    if root['entity_type'] == 'ITEM':
        details = get_item(entity_id) or {}
        details['loot_paths'] = get_item_loot_paths(entity_id)
    elif root['entity_type'] == 'CREATURE':
        details = get_creature(entity_id) or {}
    elif root['entity_type'] == 'LOOT_SOURCE':
        details = get_loot_source(entity_id) or {}
    elif root['entity_type'] == 'BLUEPRINT':
        with connection() as con:
            row = con.execute('''SELECT b.blueprint_id,b.item_id,e.canonical_name AS item_name,
                b.internal_name,b.lifecycle_status,b.verification_status
                FROM blueprints b JOIN entities e ON e.entity_id=b.item_id
                WHERE b.blueprint_id=?''', (entity_id,)).fetchone()
            details = dict(row) if row else {}
    return {'entity': root, 'details': details, 'graph': graph}
