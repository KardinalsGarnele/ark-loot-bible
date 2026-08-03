from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .database import connection
from .quality_engine import calculate_from_profile


VALID_COLORS = {"WHITE", "GREEN", "BLUE", "PURPLE", "YELLOW", "RED", "OTHER", None}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id() -> str:
    return f"LQRECALC-{uuid.uuid4().hex[:16].upper()}"


def configure_loot_source_quality(
    loot_source_id: str,
    drop_color: str | None,
    has_ring: bool | None,
    required_level: int | None,
    quality_profile_id: str | None,
) -> dict[str, Any]:
    normalized_color = drop_color.upper() if drop_color else None
    if normalized_color not in VALID_COLORS:
        raise ValueError("Unsupported drop color")
    if required_level is not None and required_level < 0:
        raise ValueError("required_level must be >= 0")

    with connection() as con:
        if not con.execute(
            "SELECT 1 FROM loot_sources WHERE loot_source_id=?",
            (loot_source_id,),
        ).fetchone():
            raise KeyError("Loot source not found")
        if quality_profile_id and not con.execute(
            "SELECT 1 FROM quality_profiles WHERE quality_profile_id=?",
            (quality_profile_id,),
        ).fetchone():
            raise KeyError("Quality profile not found")

        con.execute(
            """UPDATE loot_sources
               SET drop_color=?, has_ring=?, required_level=?, quality_profile_id=?
               WHERE loot_source_id=?""",
            (
                normalized_color,
                None if has_ring is None else int(has_ring),
                required_level,
                quality_profile_id,
                loot_source_id,
            ),
        )
        con.commit()
    return get_loot_source_quality(loot_source_id)


def set_entry_item_multiplier(
    loot_entry_id: str,
    item_quality_multiplier_percent: float | None,
) -> dict[str, Any]:
    if item_quality_multiplier_percent is not None and item_quality_multiplier_percent < 0:
        raise ValueError("item_quality_multiplier_percent must be >= 0")

    with connection() as con:
        if not con.execute(
            "SELECT 1 FROM loot_entries WHERE loot_entry_id=?",
            (loot_entry_id,),
        ).fetchone():
            raise KeyError("Loot entry not found")

        con.execute(
            """UPDATE loot_entries
               SET item_quality_multiplier_percent=?,
                   calculated_quality_min_percent=NULL,
                   calculated_quality_max_percent=NULL,
                   quality_formula_version=NULL
               WHERE loot_entry_id=?""",
            (item_quality_multiplier_percent, loot_entry_id),
        )
        con.commit()
    return get_loot_entry_quality(loot_entry_id)


def recalculate_loot_source_quality(
    loot_source_id: str,
    persist_calculation_audits: bool = False,
    notes: str | None = None,
) -> dict[str, Any]:
    with connection() as con:
        source = con.execute(
            """SELECT loot_source_id, quality_profile_id
               FROM loot_sources WHERE loot_source_id=?""",
            (loot_source_id,),
        ).fetchone()
        if not source:
            raise KeyError("Loot source not found")

        entries = con.execute(
            """SELECT le.loot_entry_id, le.item_quality_multiplier_percent
               FROM loot_entries le
               JOIN loot_sets ls ON ls.loot_set_id=le.loot_set_id
               WHERE ls.loot_source_id=?
               ORDER BY le.loot_entry_id""",
            (loot_source_id,),
        ).fetchall()

    calculated = 0
    incomplete = 0
    results = []

    for entry in entries:
        if not source["quality_profile_id"] or entry["item_quality_multiplier_percent"] is None:
            result = {
                "loot_entry_id": entry["loot_entry_id"],
                "status": "INCOMPLETE",
                "result_min_percent": None,
                "result_max_percent": None,
            }
            incomplete += 1
        else:
            calculation = calculate_from_profile(
                source["quality_profile_id"],
                entry["item_quality_multiplier_percent"],
                persist=persist_calculation_audits,
                notes=notes,
            )
            result = {
                "loot_entry_id": entry["loot_entry_id"],
                "status": calculation["status"],
                "result_min_percent": calculation["result_min_percent"],
                "result_max_percent": calculation["result_max_percent"],
                "formula_version": calculation["formula_version"],
            }
            calculated += 1

            with connection() as con:
                con.execute(
                    """UPDATE loot_entries
                       SET effective_quality_min=?,
                           effective_quality_max=?,
                           calculated_quality_min_percent=?,
                           calculated_quality_max_percent=?,
                           quality_formula_version=?
                       WHERE loot_entry_id=?""",
                    (
                        calculation["result_min_percent"],
                        calculation["result_max_percent"],
                        calculation["result_min_percent"],
                        calculation["result_max_percent"],
                        calculation["formula_version"],
                        entry["loot_entry_id"],
                    ),
                )
                con.commit()

        results.append(result)

    run_id = _id()
    with connection() as con:
        con.execute(
            """INSERT INTO loot_quality_recalculations
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                run_id,
                loot_source_id,
                source["quality_profile_id"],
                len(entries),
                calculated,
                incomplete,
                _now(),
                notes,
            ),
        )
        con.commit()

    return {
        "loot_quality_recalculation_id": run_id,
        "loot_source_id": loot_source_id,
        "quality_profile_id": source["quality_profile_id"],
        "entries_seen": len(entries),
        "entries_calculated": calculated,
        "entries_incomplete": incomplete,
        "results": results,
    }


def get_loot_source_quality(loot_source_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row = con.execute(
            """SELECT l.loot_source_id, e.canonical_name, l.drop_color, l.has_ring,
                      l.required_level, l.quality_profile_id,
                      q.profile_code, q.display_name AS quality_profile_name,
                      q.source_quality_min_percent, q.source_quality_max_percent,
                      q.verification_status AS quality_profile_verification_status
               FROM loot_sources l
               JOIN entities e ON e.entity_id=l.loot_source_id
               LEFT JOIN quality_profiles q ON q.quality_profile_id=l.quality_profile_id
               WHERE l.loot_source_id=?""",
            (loot_source_id,),
        ).fetchone()
        return dict(row) if row else None


def get_loot_entry_quality(loot_entry_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row = con.execute(
            """SELECT le.loot_entry_id, e.canonical_name,
                      le.item_quality_multiplier_percent,
                      le.effective_quality_min, le.effective_quality_max,
                      le.calculated_quality_min_percent,
                      le.calculated_quality_max_percent,
                      le.quality_formula_version,
                      ls.loot_source_id, src.drop_color, src.has_ring,
                      src.required_level, src.quality_profile_id
               FROM loot_entries le
               JOIN entities e ON e.entity_id=le.loot_entry_id
               JOIN loot_sets ls ON ls.loot_set_id=le.loot_set_id
               JOIN loot_sources src ON src.loot_source_id=ls.loot_source_id
               WHERE le.loot_entry_id=?""",
            (loot_entry_id,),
        ).fetchone()
        return dict(row) if row else None


def list_loot_quality_matrix(
    drop_color: str | None = None,
    has_ring: bool | None = None,
) -> list[dict[str, Any]]:
    clauses = []
    params: list[Any] = []
    if drop_color:
        clauses.append("src.drop_color=?")
        params.append(drop_color.upper())
    if has_ring is not None:
        clauses.append("src.has_ring=?")
        params.append(int(has_ring))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""

    with connection() as con:
        rows = con.execute(
            f"""SELECT src.loot_source_id, source_entity.canonical_name AS loot_source_name,
                       src.drop_color, src.has_ring, src.required_level,
                       src.quality_profile_id,
                       entry.loot_entry_id, entry_entity.canonical_name AS loot_entry_name,
                       entry.item_quality_multiplier_percent,
                       entry.calculated_quality_min_percent,
                       entry.calculated_quality_max_percent,
                       entry.quality_formula_version
                FROM loot_sources src
                JOIN entities source_entity ON source_entity.entity_id=src.loot_source_id
                LEFT JOIN loot_sets set_row ON set_row.loot_source_id=src.loot_source_id
                LEFT JOIN loot_entries entry ON entry.loot_set_id=set_row.loot_set_id
                LEFT JOIN entities entry_entity ON entry_entity.entity_id=entry.loot_entry_id
                {where}
                ORDER BY src.drop_color, src.has_ring, src.required_level,
                         source_entity.canonical_name, entry_entity.canonical_name""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]
