from __future__ import annotations

import uuid
from typing import Any

from .database import connection


GROUP_ORDER = [
    "SURFACE_SUPPLY",
    "CAVE",
    "DEEP_SEA",
    "FISHING",
    "CREATURE_DROP",
    "BOSS_TEK",
    "MISSION",
    "OSD",
    "WORLD",
    "OTHER",
]
VALID_GROUPS = set(GROUP_ORDER)


def _id() -> str:
    return f"MAPLOOTGROUP-{uuid.uuid4().hex[:16].upper()}"


def configure_loot_source_group(
    loot_source_id: str,
    source_group: str,
    display_order: int | None = None,
) -> dict[str, Any]:
    group = source_group.upper()
    if group not in VALID_GROUPS:
        raise ValueError("Unsupported loot source group")
    if display_order is not None and display_order < 0:
        raise ValueError("display_order must be >= 0")

    with connection() as con:
        row = con.execute(
            "SELECT map_id FROM loot_sources WHERE loot_source_id=?",
            (loot_source_id,),
        ).fetchone()
        if not row:
            raise KeyError("Loot source not found")

        con.execute(
            """UPDATE loot_sources
               SET source_group=?, display_order=?
               WHERE loot_source_id=?""",
            (group, display_order, loot_source_id),
        )
        con.execute(
            """INSERT INTO map_loot_group_status(
                 map_loot_group_status_id,map_id,source_group,group_status,
                 verification_status,notes
               ) VALUES(?,?,?,'PARTIAL','NEEDS_VERIFICATION',?)
               ON CONFLICT(map_id,source_group) DO UPDATE SET
                 group_status=CASE
                   WHEN map_loot_group_status.group_status='COMPLETE' THEN 'COMPLETE'
                   ELSE 'PARTIAL'
                 END""",
            (
                _id(),
                row["map_id"],
                group,
                "At least one structural loot source exists in this group.",
            ),
        )
        con.commit()
    return get_loot_source_group(loot_source_id)


def get_loot_source_group(loot_source_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row = con.execute(
            """SELECT l.loot_source_id,e.canonical_name,l.map_id,
                      l.source_group,l.display_order,l.source_type,
                      l.drop_color,l.has_ring,l.required_level
               FROM loot_sources l
               JOIN entities e ON e.entity_id=l.loot_source_id
               WHERE l.loot_source_id=?""",
            (loot_source_id,),
        ).fetchone()
        return dict(row) if row else None


def ensure_map_groups(map_id: str) -> list[dict[str, Any]]:
    with connection() as con:
        if not con.execute("SELECT 1 FROM maps WHERE map_id=?", (map_id,)).fetchone():
            raise KeyError("Map not found")
        for group in GROUP_ORDER:
            con.execute(
                """INSERT OR IGNORE INTO map_loot_group_status(
                     map_loot_group_status_id,map_id,source_group,group_status,
                     verification_status,notes
                   ) VALUES(?,?,?,'EMPTY','NEEDS_VERIFICATION',?)""",
                (_id(), map_id, group, "No verified group content imported yet."),
            )
        con.commit()
    return get_map_loot_groups(map_id)


def get_map_loot_groups(map_id: str) -> list[dict[str, Any]]:
    with connection() as con:
        rows = con.execute(
            """SELECT g.map_id,g.source_group,g.group_status,g.verification_status,g.notes,
                      COUNT(l.loot_source_id) AS loot_source_count,
                      SUM(CASE WHEN l.has_ring=1 THEN 1 ELSE 0 END) AS ring_source_count,
                      COUNT(DISTINCT ls.loot_set_id) AS loot_set_count,
                      COUNT(DISTINCT le.loot_entry_id) AS loot_entry_count
               FROM map_loot_group_status g
               LEFT JOIN loot_sources l
                 ON l.map_id=g.map_id AND l.source_group=g.source_group
               LEFT JOIN loot_sets ls ON ls.loot_source_id=l.loot_source_id
               LEFT JOIN loot_entries le ON le.loot_set_id=ls.loot_set_id
               WHERE g.map_id=?
               GROUP BY g.map_id,g.source_group,g.group_status,
                        g.verification_status,g.notes""",
            (map_id,),
        ).fetchall()
    values = [dict(row) for row in rows]
    values.sort(key=lambda row: GROUP_ORDER.index(row["source_group"]))
    return values


def get_grouped_loot_matrix(map_id: str, include_empty: bool = True) -> dict[str, Any]:
    groups = ensure_map_groups(map_id)
    with connection() as con:
        map_row = con.execute(
            """SELECT e.canonical_name FROM maps m
               JOIN entities e ON e.entity_id=m.map_id
               WHERE m.map_id=?""",
            (map_id,),
        ).fetchone()
        sources = [
            dict(row)
            for row in con.execute(
                """SELECT l.loot_source_id,e.canonical_name,l.source_group,
                          l.display_order,l.source_type,l.drop_color,l.has_ring,
                          l.required_level,l.verification_status,
                          COUNT(DISTINCT ls.loot_set_id) AS loot_set_count,
                          COUNT(DISTINCT le.loot_entry_id) AS loot_entry_count
                   FROM loot_sources l
                   JOIN entities e ON e.entity_id=l.loot_source_id
                   LEFT JOIN loot_sets ls ON ls.loot_source_id=l.loot_source_id
                   LEFT JOIN loot_entries le ON le.loot_set_id=ls.loot_set_id
                   WHERE l.map_id=?
                   GROUP BY l.loot_source_id,e.canonical_name,l.source_group,
                            l.display_order,l.source_type,l.drop_color,l.has_ring,
                            l.required_level,l.verification_status""",
                (map_id,),
            )
        ]

    grouped = []
    for group in groups:
        group_sources = [
            source for source in sources
            if source["source_group"] == group["source_group"]
        ]
        group_sources.sort(
            key=lambda value: (
                value["display_order"] if value["display_order"] is not None else 9999,
                value["drop_color"] or "",
                value["has_ring"] if value["has_ring"] is not None else 2,
                value["required_level"] if value["required_level"] is not None else 9999,
                value["canonical_name"].lower(),
            )
        )
        if include_empty or group_sources:
            grouped.append({**group, "sources": group_sources})

    return {
        "map_id": map_id,
        "map_name": map_row["canonical_name"] if map_row else None,
        "groups": grouped,
    }
