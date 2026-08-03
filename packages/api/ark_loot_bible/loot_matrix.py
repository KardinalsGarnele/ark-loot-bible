from __future__ import annotations

import csv
import io
import json
from typing import Any

from .database import connection


COLOR_ORDER = {
    "WHITE": 1,
    "GREEN": 2,
    "BLUE": 3,
    "PURPLE": 4,
    "YELLOW": 5,
    "RED": 6,
    "OTHER": 7,
    None: 99,
}


def _matrix_rows(
    map_id: str | None = None,
    drop_color: str | None = None,
    has_ring: bool | None = None,
    required_level_min: int | None = None,
    verification_status: str | None = None,
    source_group: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if map_id:
        clauses.append("src.map_id=?")
        params.append(map_id)
    if drop_color:
        clauses.append("src.drop_color=?")
        params.append(drop_color.upper())
    if has_ring is not None:
        clauses.append("src.has_ring=?")
        params.append(int(has_ring))
    if required_level_min is not None:
        clauses.append("COALESCE(src.required_level, -1) >= ?")
        params.append(required_level_min)
    if verification_status:
        clauses.append("entry.verification_status=?")
        params.append(verification_status)
    if source_group:
        clauses.append("src.source_group=?")
        params.append(source_group.upper())

    where = "WHERE " + " AND ".join(clauses) if clauses else ""

    with connection() as con:
        rows = con.execute(
            f"""SELECT
                    src.map_id,
                    map_entity.canonical_name AS map_name,
                    src.loot_source_id,
                    source_entity.canonical_name AS loot_source_name,
                    src.source_type,
                    src.source_group,
                    src.drop_color,
                    src.has_ring,
                    src.required_level,
                    src.verification_status AS loot_source_verification_status,
                    src.quality_profile_id,
                    qp.display_name AS quality_profile_name,
                    qp.source_quality_min_percent,
                    qp.source_quality_max_percent,
                    set_row.loot_set_id,
                    set_entity.canonical_name AS loot_set_name,
                    entry.loot_entry_id,
                    entry_entity.canonical_name AS loot_entry_name,
                    item_entity.canonical_name AS item_name,
                    blueprint_entity.canonical_name AS blueprint_name,
                    entry.entry_weight,
                    entry.min_quantity,
                    entry.max_quantity,
                    entry.blueprint_chance,
                    entry.item_quality_multiplier_percent,
                    entry.calculated_quality_min_percent,
                    entry.calculated_quality_max_percent,
                    entry.quality_formula_version,
                    entry.verification_status AS loot_entry_verification_status
                FROM loot_sources src
                JOIN entities source_entity ON source_entity.entity_id=src.loot_source_id
                LEFT JOIN maps map_row ON map_row.map_id=src.map_id
                LEFT JOIN entities map_entity ON map_entity.entity_id=map_row.map_id
                LEFT JOIN quality_profiles qp ON qp.quality_profile_id=src.quality_profile_id
                LEFT JOIN loot_sets set_row ON set_row.loot_source_id=src.loot_source_id
                LEFT JOIN entities set_entity ON set_entity.entity_id=set_row.loot_set_id
                LEFT JOIN loot_entries entry ON entry.loot_set_id=set_row.loot_set_id
                LEFT JOIN entities entry_entity ON entry_entity.entity_id=entry.loot_entry_id
                LEFT JOIN items item_row ON item_row.item_id=entry.item_id
                LEFT JOIN entities item_entity ON item_entity.entity_id=item_row.item_id
                LEFT JOIN blueprints blueprint_row ON blueprint_row.blueprint_id=entry.blueprint_id
                LEFT JOIN entities blueprint_entity ON blueprint_entity.entity_id=blueprint_row.blueprint_id
                {where}""",
            params,
        ).fetchall()

    values = [dict(row) for row in rows]
    values.sort(
        key=lambda row: (
            (row.get("map_name") or "").lower(),
            COLOR_ORDER.get(row.get("drop_color"), 99),
            0 if row.get("has_ring") == 0 else 1 if row.get("has_ring") == 1 else 2,
            row.get("required_level") if row.get("required_level") is not None else 9999,
            (row.get("loot_source_name") or "").lower(),
            (row.get("loot_set_name") or "").lower(),
            (row.get("loot_entry_name") or "").lower(),
        )
    )
    return values


def get_loot_matrix(**filters: Any) -> dict[str, Any]:
    rows = _matrix_rows(**filters)
    return {
        "row_count": len(rows),
        "filters": filters,
        "rows": rows,
    }


def export_loot_matrix_csv(**filters: Any) -> str:
    rows = _matrix_rows(**filters)
    output = io.StringIO()
    fieldnames = [
        "map_name",
        "drop_color",
        "has_ring",
        "required_level",
        "loot_source_name",
        "source_type",
        "source_group",
        "quality_profile_name",
        "source_quality_min_percent",
        "source_quality_max_percent",
        "loot_set_name",
        "loot_entry_name",
        "item_name",
        "blueprint_name",
        "entry_weight",
        "min_quantity",
        "max_quantity",
        "blueprint_chance",
        "item_quality_multiplier_percent",
        "calculated_quality_min_percent",
        "calculated_quality_max_percent",
        "quality_formula_version",
        "loot_entry_verification_status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key) for key in fieldnames})
    return output.getvalue()


def export_loot_matrix_json(**filters: Any) -> str:
    return json.dumps(get_loot_matrix(**filters), indent=2, ensure_ascii=False)
