from __future__ import annotations
from typing import Any
from .database import connection
from .review import get_review_case
from .promotion import preview_promotion


def _scalar(con, sql: str, params: tuple = ()) -> int:
    return int(con.execute(sql, params).fetchone()[0])


def get_steward_summary() -> dict[str, Any]:
    with connection() as con:
        review_counts = {r["case_status"]: r["count"] for r in con.execute(
            "SELECT case_status, COUNT(*) AS count FROM review_cases GROUP BY case_status"
        )}
        run_counts = {r["status"]: r["count"] for r in con.execute(
            "SELECT status, COUNT(*) AS count FROM ingestion_runs GROUP BY status"
        )}
        return {
            "imports": {
                "runs": _scalar(con, "SELECT COUNT(*) FROM ingestion_runs"),
                "records": _scalar(con, "SELECT COUNT(*) FROM import_records"),
                "staged_claims": _scalar(con, "SELECT COUNT(*) FROM claim_candidates"),
                "statuses": run_counts,
            },
            "reviews": {
                "total": _scalar(con, "SELECT COUNT(*) FROM review_cases"),
                "open": review_counts.get("OPEN", 0),
                "conflict": review_counts.get("CONFLICT", 0),
                "approved": review_counts.get("APPROVED", 0),
                "promoted": review_counts.get("PROMOTED", 0),
                "rejected": review_counts.get("REJECTED", 0),
            },
            "canonical": {
                "maps": _scalar(con, "SELECT COUNT(*) FROM maps"),
                "items": _scalar(con, "SELECT COUNT(*) FROM items"),
                "creatures": _scalar(con, "SELECT COUNT(*) FROM creatures"),
                "revisions": _scalar(con, "SELECT COUNT(*) FROM canonical_revisions"),
            },
            "quality_gate": {
                "unresolved_conflicts": _scalar(con, "SELECT COUNT(*) FROM claim_conflicts WHERE conflict_status='OPEN'"),
                "quarantined_claims": _scalar(con, "SELECT COUNT(*) FROM quarantine_records WHERE resolved_at IS NULL"),
                "failed_promotions": _scalar(con, "SELECT COUNT(*) FROM canonical_promotion_attempts WHERE attempt_status='FAILED'"),
            },
        }


def list_ingestion_runs(limit: int = 50) -> list[dict[str, Any]]:
    with connection() as con:
        rows = con.execute(
            """SELECT r.*, COUNT(DISTINCT m.message_id) AS message_count
               FROM ingestion_runs r
               LEFT JOIN ingestion_messages m ON m.run_id=r.run_id
               GROUP BY r.run_id
               ORDER BY r.started_at DESC LIMIT ?""", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_review_workspace(review_case_id: str) -> dict[str, Any] | None:
    case = get_review_case(review_case_id)
    if case is None:
        return None
    preview = None
    preview_error = None
    if case["case_status"] in {"APPROVED", "PROMOTED"}:
        try:
            preview = preview_promotion(review_case_id, "steward-console")
        except (KeyError, ValueError) as exc:
            preview_error = str(exc)
    with connection() as con:
        record = con.execute("SELECT * FROM import_records WHERE import_record_id=?", (case["import_record_id"],)).fetchone()
        run = None
        if record:
            batch = con.execute("SELECT * FROM import_batches WHERE import_batch_id=?", (record["import_batch_id"],)).fetchone()
            if batch:
                run = con.execute("SELECT * FROM ingestion_runs WHERE source_version_id=? ORDER BY started_at DESC LIMIT 1", (batch["source_version_id"],)).fetchone()
        revisions = []
        entity_id = case.get("proposed_entity_id") or (record["proposed_entity_id"] if record else None)
        if entity_id:
            revisions = [dict(r) for r in con.execute(
                "SELECT revision_id,entity_id,entity_type,revision_number,operation,promoted_by,promoted_at FROM canonical_revisions WHERE entity_id=? ORDER BY revision_number DESC",
                (entity_id,)
            )]
    return {
        "case": case,
        "import_record": dict(record) if record else None,
        "ingestion_run": dict(run) if run else None,
        "promotion_preview": preview,
        "promotion_preview_error": preview_error,
        "revisions": revisions,
    }
