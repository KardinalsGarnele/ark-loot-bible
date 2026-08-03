from __future__ import annotations
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any
from .database import connection

POLICY_VERSION = "canonical-promotion/1.0"

FIELD_POLICIES: dict[str, dict[str, set[str]]] = {
    "MAP": {
        "required": {"canonical_name", "game_title", "map_kind", "included_with_base_game", "official"},
        "allowed": {"canonical_name", "game_title", "map_kind", "included_with_base_game", "official", "internal_name", "release_status"},
    },
    "ITEM": {
        "required": {"canonical_name", "game_title", "category_code"},
        "allowed": {"canonical_name", "game_title", "category_code", "internal_name", "description", "stack_size", "weight", "quality_capable", "item_category"},
    },
    "CREATURE": {
        "required": {"canonical_name", "game_title"},
        "allowed": {"canonical_name", "game_title", "species_name", "internal_name", "description", "diet_type", "temperament", "tameable", "breedable"},
    },
}
PREFIXES = {"MAP": "MAP-", "ITEM": "ITEM-", "CREATURE": "CREATURE-"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


def _bool(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    v = str(value).strip().lower()
    if v in {"1", "true", "yes", "y"}: return 1
    if v in {"0", "false", "no", "n"}: return 0
    raise ValueError(f"Invalid boolean value: {value}")


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "": return None
    return int(value)


def _float(value: Any) -> float | None:
    if value is None or str(value).strip() == "": return None
    return float(value)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _review_payload(con: sqlite3.Connection, review_case_id: str) -> tuple[sqlite3.Row, sqlite3.Row, dict[str, str]]:
    case = con.execute("SELECT * FROM review_cases WHERE review_case_id=?", (review_case_id,)).fetchone()
    if not case:
        raise KeyError("Review case not found")
    if case["case_status"] == "PROMOTED":
        revision = con.execute("SELECT * FROM canonical_revisions WHERE review_case_id=?", (review_case_id,)).fetchone()
        if revision:
            return case, con.execute("SELECT * FROM import_records WHERE import_record_id=?", (case["import_record_id"],)).fetchone(), {}
    if case["case_status"] != "APPROVED":
        raise ValueError("Review case must be APPROVED before promotion")
    rec = con.execute("SELECT * FROM import_records WHERE import_record_id=?", (case["import_record_id"],)).fetchone()
    rows = con.execute("""
        SELECT c.field_name, c.claim_value, r.normalized_value, r.reviewed_at
        FROM claim_candidates c
        JOIN claim_reviews r ON r.claim_candidate_id=c.claim_candidate_id AND r.review_case_id=?
        WHERE c.import_record_id=? AND r.decision='ACCEPT'
        ORDER BY c.field_name, r.reviewed_at DESC
    """, (review_case_id, case["import_record_id"])).fetchall()
    claims: dict[str, str] = {}
    for row in rows:
        claims.setdefault(row["field_name"], row["normalized_value"] if row["normalized_value"] is not None else row["claim_value"])
    total = con.execute("SELECT COUNT(DISTINCT field_name) FROM claim_candidates WHERE import_record_id=?", (case["import_record_id"],)).fetchone()[0]
    if len(claims) != total:
        raise ValueError("Every claim field must have an accepted review")
    return case, rec, claims


def _current_snapshot(con: sqlite3.Connection, entity_id: str, entity_type: str) -> dict[str, Any] | None:
    entity = con.execute("SELECT * FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
    if not entity:
        return None
    if entity["entity_type"] != entity_type:
        raise ValueError("Stable ID already belongs to a different entity type")
    snap: dict[str, Any] = {"entity": dict(entity)}
    table = {"MAP": "maps", "ITEM": "items", "CREATURE": "creatures"}[entity_type]
    key = {"MAP": "map_id", "ITEM": "item_id", "CREATURE": "creature_id"}[entity_type]
    row = con.execute(f"SELECT * FROM {table} WHERE {key}=?", (entity_id,)).fetchone()
    snap[table[:-1] if table.endswith('s') else table] = dict(row) if row else None
    if entity_type == "ITEM":
        snap["categories"] = [dict(r) for r in con.execute("SELECT * FROM item_category_assignments WHERE item_id=? ORDER BY category_code", (entity_id,))]
    return snap


def _proposed_snapshot(entity_id: str, entity_type: str, claims: dict[str, str], current: dict[str, Any] | None) -> dict[str, Any]:
    policy = FIELD_POLICIES.get(entity_type)
    if not policy:
        raise ValueError(f"Unsupported entity type: {entity_type}")
    unknown = set(claims) - policy["allowed"]
    if unknown:
        raise ValueError(f"Unsupported {entity_type} fields: {sorted(unknown)}")
    missing = policy["required"] - set(claims)
    if missing and current is None:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    if not entity_id or not entity_id.startswith(PREFIXES[entity_type]):
        raise ValueError(f"Stable {entity_type} ID with prefix {PREFIXES[entity_type]} is required")
    base_entity = dict((current or {}).get("entity") or {})
    name = claims.get("canonical_name", base_entity.get("canonical_name"))
    if not name: raise ValueError("canonical_name is required")
    entity = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "canonical_name": name,
        "slug": _slug(name),
        "verification_status": "VERIFIED",
    }
    if entity_type == "MAP":
        old = dict((current or {}).get("map") or {})
        domain = {
            "map_id": entity_id,
            "internal_name": claims.get("internal_name", old.get("internal_name")),
            "release_status": claims.get("release_status", old.get("release_status")),
            "official": _bool(claims.get("official", old.get("official"))),
            "game_title": claims.get("game_title", old.get("game_title")),
            "map_kind": claims.get("map_kind", old.get("map_kind")),
            "included_with_base_game": _bool(claims.get("included_with_base_game", old.get("included_with_base_game"))),
            "lifecycle_status": old.get("lifecycle_status", "ACTIVE"),
        }
        return {"entity": entity, "map": domain}
    if entity_type == "ITEM":
        old = dict((current or {}).get("item") or {})
        category = claims.get("category_code", claims.get("item_category", old.get("item_category")))
        domain = {
            "item_id": entity_id,
            "item_category": category,
            "quality_capable": _bool(claims.get("quality_capable", old.get("quality_capable"))),
            "game_title": claims.get("game_title", old.get("game_title")),
            "internal_name": claims.get("internal_name", old.get("internal_name")),
            "description": claims.get("description", old.get("description")),
            "stack_size": _int(claims.get("stack_size", old.get("stack_size"))),
            "weight": _float(claims.get("weight", old.get("weight"))),
            "lifecycle_status": old.get("lifecycle_status", "ACTIVE"),
        }
        return {"entity": entity, "item": domain, "primary_category": category}
    old = dict((current or {}).get("creature") or {})
    domain = {
        "creature_id": entity_id,
        "species_name": claims.get("species_name", old.get("species_name")),
        "tameable": _bool(claims.get("tameable", old.get("tameable"))),
        "breedable": _bool(claims.get("breedable", old.get("breedable"))),
        "game_title": claims.get("game_title", old.get("game_title")),
        "internal_name": claims.get("internal_name", old.get("internal_name")),
        "description": claims.get("description", old.get("description")),
        "diet_type": claims.get("diet_type", old.get("diet_type")),
        "temperament": claims.get("temperament", old.get("temperament")),
        "lifecycle_status": old.get("lifecycle_status", "ACTIVE"),
    }
    return {"entity": entity, "creature": domain}


def _diff(current: dict[str, Any] | None, proposed: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    current = current or {}
    for section, values in proposed.items():
        if not isinstance(values, dict):
            old = current.get(section)
            if old != values: changes.append({"section": section, "field": section, "old": old, "new": values})
            continue
        old_values = current.get(section) or {}
        for field, new in values.items():
            if field in {"created_at", "updated_at"}: continue
            old = old_values.get(field)
            if old != new:
                changes.append({"section": section, "field": field, "old": old, "new": new})
    return changes


def preview_promotion(review_case_id: str, actor: str = "promotion-preview") -> dict[str, Any]:
    with connection() as con:
        case, rec, claims = _review_payload(con, review_case_id)
        existing_revision = con.execute("SELECT * FROM canonical_revisions WHERE review_case_id=?", (review_case_id,)).fetchone()
        if existing_revision:
            return {"review_case_id": review_case_id, "entity_id": existing_revision["entity_id"], "entity_type": existing_revision["entity_type"], "status": "ALREADY_PROMOTED", "changes": []}
        entity_id = case["proposed_entity_id"] or rec["proposed_entity_id"]
        entity_type = case["entity_type"]
        current = _current_snapshot(con, entity_id, entity_type)
        proposed = _proposed_snapshot(entity_id, entity_type, claims, current)
        changes = _diff(current, proposed)
        status = "READY" if changes else "NO_CHANGES"
        con.execute("INSERT INTO canonical_promotion_attempts VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (_id("PATT"), review_case_id, entity_id, entity_type, "PREVIEW", "SUCCEEDED" if changes else "NO_CHANGES", json.dumps(changes, sort_keys=True), actor, _now(), None))
        con.commit()
        return {"review_case_id": review_case_id, "entity_id": entity_id, "entity_type": entity_type, "operation": "CREATE" if current is None else "UPDATE", "status": status, "changes": changes, "proposed": proposed}


def _write_entity(con: sqlite3.Connection, entity_type: str, snapshot: dict[str, Any], now: str) -> None:
    e = snapshot["entity"]
    exists = con.execute("SELECT 1 FROM entities WHERE entity_id=?", (e["entity_id"],)).fetchone()
    if exists:
        con.execute("UPDATE entities SET canonical_name=?,slug=?,verification_status='VERIFIED',updated_at=? WHERE entity_id=?", (e["canonical_name"], e["slug"], now, e["entity_id"]))
    else:
        con.execute("INSERT INTO entities(entity_id,entity_type,canonical_name,slug,verification_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (e["entity_id"], entity_type, e["canonical_name"], e["slug"], "VERIFIED", now, now))
    if entity_type == "MAP":
        d=snapshot["map"]
        con.execute("""INSERT INTO maps(map_id,internal_name,release_status,official,game_title,map_kind,included_with_base_game,lifecycle_status)
            VALUES(:map_id,:internal_name,:release_status,:official,:game_title,:map_kind,:included_with_base_game,:lifecycle_status)
            ON CONFLICT(map_id) DO UPDATE SET internal_name=excluded.internal_name,release_status=excluded.release_status,
            official=excluded.official,game_title=excluded.game_title,map_kind=excluded.map_kind,
            included_with_base_game=excluded.included_with_base_game,lifecycle_status=excluded.lifecycle_status""", d)
    elif entity_type == "ITEM":
        d=snapshot["item"]
        con.execute("""INSERT INTO items(item_id,item_category,quality_capable,game_title,internal_name,description,stack_size,weight,lifecycle_status)
            VALUES(:item_id,:item_category,:quality_capable,:game_title,:internal_name,:description,:stack_size,:weight,:lifecycle_status)
            ON CONFLICT(item_id) DO UPDATE SET item_category=excluded.item_category,quality_capable=excluded.quality_capable,
            game_title=excluded.game_title,internal_name=excluded.internal_name,description=excluded.description,
            stack_size=excluded.stack_size,weight=excluded.weight,lifecycle_status=excluded.lifecycle_status""", d)
        category=snapshot.get("primary_category")
        if category:
            if not con.execute("SELECT 1 FROM item_categories WHERE category_code=?", (category,)).fetchone():
                raise ValueError(f"Unknown item category: {category}")
            con.execute("UPDATE item_category_assignments SET is_primary=0 WHERE item_id=?", (d["item_id"],))
            con.execute("""INSERT INTO item_category_assignments(item_id,category_code,is_primary,assigned_at) VALUES(?,?,1,?)
                ON CONFLICT(item_id,category_code) DO UPDATE SET is_primary=1,assigned_at=excluded.assigned_at""", (d["item_id"], category, now))
    else:
        d=snapshot["creature"]
        con.execute("""INSERT INTO creatures(creature_id,species_name,tameable,breedable,game_title,internal_name,description,diet_type,temperament,lifecycle_status)
            VALUES(:creature_id,:species_name,:tameable,:breedable,:game_title,:internal_name,:description,:diet_type,:temperament,:lifecycle_status)
            ON CONFLICT(creature_id) DO UPDATE SET species_name=excluded.species_name,tameable=excluded.tameable,
            breedable=excluded.breedable,game_title=excluded.game_title,internal_name=excluded.internal_name,
            description=excluded.description,diet_type=excluded.diet_type,temperament=excluded.temperament,lifecycle_status=excluded.lifecycle_status""", d)


def promote_review(review_case_id: str, actor: str, expected_row_version: int | None = None) -> dict[str, Any]:
    with connection() as con:
        try:
            con.execute("BEGIN IMMEDIATE")
            case, rec, claims = _review_payload(con, review_case_id)
            prior = con.execute("SELECT * FROM canonical_revisions WHERE review_case_id=?", (review_case_id,)).fetchone()
            if prior:
                con.rollback()
                return {"status": "ALREADY_PROMOTED", "revision_id": prior["revision_id"], "entity_id": prior["entity_id"], "revision_number": prior["revision_number"]}
            if expected_row_version is not None and case["row_version"] != expected_row_version:
                raise ValueError("Review case changed since preview; refresh before promotion")
            entity_id = case["proposed_entity_id"] or rec["proposed_entity_id"]
            entity_type = case["entity_type"]
            current = _current_snapshot(con, entity_id, entity_type)
            proposed = _proposed_snapshot(entity_id, entity_type, claims, current)
            changes = _diff(current, proposed)
            if not changes:
                con.execute("INSERT INTO canonical_promotion_attempts VALUES(?,?,?,?,?,?,?,?,?,?)", (_id("PATT"),review_case_id,entity_id,entity_type,"COMMIT","NO_CHANGES",json.dumps([]),actor,_now(),None))
                con.commit()
                return {"status":"NO_CHANGES","entity_id":entity_id,"changes":[]}
            now=_now()
            _write_entity(con, entity_type, proposed, now)
            source = con.execute("""SELECT s.source_id FROM import_batches b JOIN source_versions v ON v.source_version_id=b.source_version_id
                JOIN sources s ON s.source_id=v.source_id WHERE b.import_batch_id=?""", (rec["import_batch_id"],)).fetchone()[0]
            for field, value in claims.items():
                con.execute("UPDATE field_evidence_links SET is_current=0 WHERE entity_id=? AND field_name=?", (entity_id, field))
                evid=_id("EVID")
                con.execute("INSERT INTO evidence(evidence_id,entity_id,source_id,field_name,claim_value,verification_status,valid_from,notes) VALUES(?,?,?,?,?,'VERIFIED',?,?)", (evid,entity_id,source,field,value,now,f"Promoted from review case {review_case_id}"))
                con.execute("INSERT INTO field_evidence_links(field_evidence_id,entity_id,field_name,evidence_id,is_current,linked_at) VALUES(?,?,?,?,1,?)", (_id("FEV"),entity_id,field,evid,now))
            revision_number = con.execute("SELECT COALESCE(MAX(revision_number),0)+1 FROM canonical_revisions WHERE entity_id=?", (entity_id,)).fetchone()[0]
            revision_id=_id("REV")
            con.execute("INSERT INTO canonical_revisions VALUES(?,?,?,?,?,?,?,?,?,?)", (revision_id,entity_id,entity_type,revision_number,review_case_id,"CREATE" if current is None else "UPDATE",json.dumps(current,sort_keys=True) if current else None,json.dumps(proposed,sort_keys=True),actor,now))
            con.execute("INSERT INTO canonical_promotion_attempts VALUES(?,?,?,?,?,?,?,?,?,?)", (_id("PATT"),review_case_id,entity_id,entity_type,"COMMIT","SUCCEEDED",json.dumps(changes,sort_keys=True),actor,now,None))
            con.execute("UPDATE review_cases SET case_status='PROMOTED',closed_at=?,updated_at=?,row_version=row_version+1 WHERE review_case_id=?", (now,now,review_case_id))
            con.execute("UPDATE import_records SET proposed_entity_id=?,record_status='PROMOTED' WHERE import_record_id=?", (entity_id,case["import_record_id"]))
            con.execute("UPDATE claim_candidates SET candidate_status='PROMOTED' WHERE import_record_id=?", (case["import_record_id"],))
            con.execute("INSERT INTO promotion_log VALUES(?,?,?,?,?,?)", (_id("PROMO"),case["import_record_id"],entity_id,now,actor,f"{POLICY_VERSION}; review={review_case_id}"))
            con.commit()
            return {"status":"PROMOTED","revision_id":revision_id,"entity_id":entity_id,"entity_type":entity_type,"revision_number":revision_number,"operation":"CREATE" if current is None else "UPDATE","changes":changes}
        except Exception as exc:
            con.rollback()
            try:
                con.execute("INSERT INTO canonical_promotion_attempts VALUES(?,?,?,?,?,?,?,?,?,?)", (_id("PATT"),review_case_id,None,"UNKNOWN","COMMIT","FAILED",None,actor,_now(),str(exc)))
                con.commit()
            except Exception:
                con.rollback()
            raise


def get_revisions(entity_id: str) -> list[dict[str, Any]]:
    with connection() as con:
        return [dict(r) for r in con.execute("SELECT revision_id,entity_id,entity_type,revision_number,review_case_id,operation,promoted_by,promoted_at FROM canonical_revisions WHERE entity_id=? ORDER BY revision_number DESC", (entity_id,))]
