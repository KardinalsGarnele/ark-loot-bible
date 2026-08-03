from __future__ import annotations

from typing import Any

from .database import connection


def search_blueprints(
    query: str | None = None,
    map_id: str | None = None,
    source_group: str | None = None,
    drop_color: str | None = None,
    has_ring: bool | None = None,
    required_level_max: int | None = None,
    verification_status: str | None = None,
) -> dict[str, Any]:
    clauses = []
    params: list[Any] = []

    if query:
        clauses.append("(lower(bp_entity.canonical_name) LIKE ? OR lower(item_entity.canonical_name) LIKE ?)")
        token = f"%{query.lower()}%"
        params.extend([token, token])
    if map_id:
        clauses.append("src.map_id=?")
        params.append(map_id)
    if source_group:
        clauses.append("src.source_group=?")
        params.append(source_group.upper())
    if drop_color:
        clauses.append("src.drop_color=?")
        params.append(drop_color.upper())
    if has_ring is not None:
        clauses.append("src.has_ring=?")
        params.append(int(has_ring))
    if required_level_max is not None:
        clauses.append("(src.required_level IS NULL OR src.required_level<=?)")
        params.append(required_level_max)
    if verification_status:
        clauses.append("entry.verification_status=?")
        params.append(verification_status)

    where = "WHERE " + " AND ".join(clauses) if clauses else ""

    with connection() as con:
        rows = con.execute(
            f"""SELECT
                    bp.blueprint_id,
                    bp_entity.canonical_name AS blueprint_name,
                    bp.verification_status AS blueprint_verification_status,
                    item.item_id,
                    item_entity.canonical_name AS item_name,
                    item.item_category,
                    item.quality_capable,
                    src.map_id,
                    map_entity.canonical_name AS map_name,
                    src.loot_source_id,
                    source_entity.canonical_name AS loot_source_name,
                    src.source_group,
                    src.source_type,
                    src.drop_color,
                    src.has_ring,
                    src.required_level,
                    set_row.loot_set_id,
                    set_entity.canonical_name AS loot_set_name,
                    entry.loot_entry_id,
                    entry_entity.canonical_name AS loot_entry_name,
                    entry.entry_weight,
                    entry.blueprint_chance,
                    entry.item_quality_multiplier_percent,
                    entry.calculated_quality_min_percent,
                    entry.calculated_quality_max_percent,
                    entry.quality_formula_version,
                    entry.verification_status AS loot_entry_verification_status,
                    qp.quality_profile_id,
                    qp.display_name AS quality_profile_name,
                    qp.source_quality_min_percent,
                    qp.source_quality_max_percent
                FROM blueprints bp
                JOIN entities bp_entity ON bp_entity.entity_id=bp.blueprint_id
                JOIN items item ON item.item_id=bp.item_id
                JOIN entities item_entity ON item_entity.entity_id=item.item_id
                LEFT JOIN loot_entries entry ON entry.blueprint_id=bp.blueprint_id
                LEFT JOIN entities entry_entity ON entry_entity.entity_id=entry.loot_entry_id
                LEFT JOIN loot_sets set_row ON set_row.loot_set_id=entry.loot_set_id
                LEFT JOIN entities set_entity ON set_entity.entity_id=set_row.loot_set_id
                LEFT JOIN loot_sources src ON src.loot_source_id=set_row.loot_source_id
                LEFT JOIN entities source_entity ON source_entity.entity_id=src.loot_source_id
                LEFT JOIN maps map_row ON map_row.map_id=src.map_id
                LEFT JOIN entities map_entity ON map_entity.entity_id=map_row.map_id
                LEFT JOIN quality_profiles qp ON qp.quality_profile_id=src.quality_profile_id
                {where}
                ORDER BY bp_entity.canonical_name,
                         map_entity.canonical_name,
                         src.source_group,
                         src.drop_color,
                         src.has_ring,
                         src.required_level,
                         source_entity.canonical_name""",
            params,
        ).fetchall()

    grouped: dict[str, dict[str, Any]] = {}
    for raw in rows:
        row = dict(raw)
        blueprint_id = row["blueprint_id"]
        blueprint = grouped.setdefault(
            blueprint_id,
            {
                "blueprint_id": blueprint_id,
                "blueprint_name": row["blueprint_name"],
                "blueprint_verification_status": row["blueprint_verification_status"],
                "item_id": row["item_id"],
                "item_name": row["item_name"],
                "item_category": row["item_category"],
                "quality_capable": row["quality_capable"],
                "source_count": 0,
                "maps": [],
                "loot_paths": [],
            },
        )

        if row["loot_source_id"] is None:
            continue

        blueprint["loot_paths"].append(
            {
                "map_id": row["map_id"],
                "map_name": row["map_name"],
                "loot_source_id": row["loot_source_id"],
                "loot_source_name": row["loot_source_name"],
                "source_group": row["source_group"],
                "source_type": row["source_type"],
                "drop_color": row["drop_color"],
                "has_ring": row["has_ring"],
                "required_level": row["required_level"],
                "loot_set_id": row["loot_set_id"],
                "loot_set_name": row["loot_set_name"],
                "loot_entry_id": row["loot_entry_id"],
                "loot_entry_name": row["loot_entry_name"],
                "entry_weight": row["entry_weight"],
                "blueprint_chance": row["blueprint_chance"],
                "item_quality_multiplier_percent": row["item_quality_multiplier_percent"],
                "calculated_quality_min_percent": row["calculated_quality_min_percent"],
                "calculated_quality_max_percent": row["calculated_quality_max_percent"],
                "quality_formula_version": row["quality_formula_version"],
                "loot_entry_verification_status": row["loot_entry_verification_status"],
                "quality_profile_id": row["quality_profile_id"],
                "quality_profile_name": row["quality_profile_name"],
                "source_quality_min_percent": row["source_quality_min_percent"],
                "source_quality_max_percent": row["source_quality_max_percent"],
            }
        )

    for blueprint in grouped.values():
        unique_sources = {
            path["loot_source_id"] for path in blueprint["loot_paths"]
            if path["loot_source_id"] is not None
        }
        unique_maps = {}
        for path in blueprint["loot_paths"]:
            if path["map_id"]:
                unique_maps[path["map_id"]] = {
                    "map_id": path["map_id"],
                    "map_name": path["map_name"],
                }
        blueprint["source_count"] = len(unique_sources)
        blueprint["maps"] = sorted(unique_maps.values(), key=lambda x: x["map_name"] or "")

    return {
        "query": query,
        "result_count": len(grouped),
        "results": list(grouped.values()),
    }


def get_blueprint_profile(blueprint_id: str) -> dict[str, Any] | None:
    result = search_blueprints()
    for blueprint in result["results"]:
        if blueprint["blueprint_id"] == blueprint_id:
            with connection() as con:
                locations = [
                    dict(row)
                    for row in con.execute(
                        """SELECT DISTINCT l.*,r.display_name AS region_name
                           FROM loot_source_locations l
                           LEFT JOIN map_regions r ON r.map_region_id=l.map_region_id
                           JOIN loot_sets ls ON ls.loot_source_id=l.loot_source_id
                           JOIN loot_entries le ON le.loot_set_id=ls.loot_set_id
                           WHERE le.blueprint_id=?
                           ORDER BY l.map_id,l.location_type,l.latitude,l.longitude""",
                        (blueprint_id,),
                    )
                ]
                respawn = [
                    dict(row)
                    for row in con.execute(
                        """SELECT DISTINCT rp.*
                           FROM loot_source_respawn_profiles rp
                           JOIN loot_sets ls ON ls.loot_source_id=rp.loot_source_id
                           JOIN loot_entries le ON le.loot_set_id=ls.loot_set_id
                           WHERE le.blueprint_id=?
                           ORDER BY rp.loot_source_id""",
                        (blueprint_id,),
                    )
                ]
            return {
                **blueprint,
                "locations": locations,
                "respawn_profiles": respawn,
            }
    return None
