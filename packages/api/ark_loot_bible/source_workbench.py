from __future__ import annotations

import difflib
import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from .config import ROOT
from .database import connection


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


def _snapshot_path(source_id: str, digest: str) -> Path:
    path = ROOT / "imports" / "source-snapshots" / source_id
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{digest}.txt"


def list_sources(stale_days: int = 30, stale_only: bool = False) -> list[dict[str, Any]]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=stale_days)).replace(microsecond=0).isoformat()
    with connection() as con:
        rows = con.execute(
            """SELECT s.*,
                      sv.source_version_id AS latest_source_version_id,
                      sv.version_label AS latest_version_label,
                      sv.content_hash_sha256 AS latest_content_hash_sha256,
                      sv.retrieved_at AS latest_retrieved_at,
                      hc.check_status AS latest_check_status,
                      hc.checked_at AS latest_checked_at,
                      hc.http_status AS latest_http_status,
                      (SELECT COUNT(*) FROM source_versions x WHERE x.source_id=s.source_id) AS version_count,
                      (SELECT COUNT(*) FROM claim_source_evidence ce
                         JOIN source_versions cev ON cev.source_version_id=ce.source_version_id
                        WHERE cev.source_id=s.source_id) AS claim_link_count
               FROM sources s
               LEFT JOIN source_versions sv ON sv.source_version_id=(
                   SELECT x.source_version_id FROM source_versions x
                   WHERE x.source_id=s.source_id ORDER BY x.retrieved_at DESC, x.source_version_id DESC LIMIT 1
               )
               LEFT JOIN source_health_checks hc ON hc.source_health_check_id=(
                   SELECT x.source_health_check_id FROM source_health_checks x
                   WHERE x.source_id=s.source_id ORDER BY x.checked_at DESC, x.source_health_check_id DESC LIMIT 1
               )
               ORDER BY COALESCE(sv.retrieved_at, s.captured_at, '') ASC, s.title"""
        ).fetchall()
        values = []
        for row in rows:
            item = dict(row)
            reference_time = item.get("latest_retrieved_at") or item.get("captured_at")
            item["is_stale"] = reference_time is None or reference_time < cutoff
            if not stale_only or item["is_stale"]:
                values.append(item)
        return values


def get_source_workspace(source_id: str) -> dict[str, Any] | None:
    with connection() as con:
        source = con.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
        if not source:
            return None
        versions = [dict(r) for r in con.execute(
            "SELECT * FROM source_versions WHERE source_id=? ORDER BY retrieved_at DESC, source_version_id DESC",
            (source_id,)
        )]
        checks = [dict(r) for r in con.execute(
            "SELECT * FROM source_health_checks WHERE source_id=? ORDER BY checked_at DESC LIMIT 30",
            (source_id,)
        )]
        links = [dict(r) for r in con.execute(
            """SELECT ce.*, c.field_name, c.claim_value, ir.proposed_canonical_name, ir.entity_type
               FROM claim_source_evidence ce
               JOIN claim_candidates c ON c.claim_candidate_id=ce.claim_candidate_id
               JOIN import_records ir ON ir.import_record_id=c.import_record_id
               JOIN source_versions sv ON sv.source_version_id=ce.source_version_id
               WHERE sv.source_id=? ORDER BY ce.linked_at DESC""",
            (source_id,)
        )]
        comparisons = [dict(r) for r in con.execute(
            "SELECT * FROM source_version_comparisons WHERE source_id=? ORDER BY compared_at DESC LIMIT 30",
            (source_id,)
        )]
        return {
            "source": dict(source),
            "versions": versions,
            "health_checks": checks,
            "claim_links": links,
            "comparisons": comparisons,
        }


def register_source(source_id: str, source_type: str, title: str, locator: str | None,
                    publisher: str | None, notes: str | None) -> dict[str, Any]:
    now = _now()
    with connection() as con:
        con.execute(
            """INSERT INTO sources(source_id,source_type,title,locator,publisher,captured_at,notes)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET source_type=excluded.source_type,
                 title=excluded.title,locator=excluded.locator,publisher=excluded.publisher,
                 notes=excluded.notes""",
            (source_id, source_type, title, locator, publisher, now, notes)
        )
        con.commit()
    return get_source_workspace(source_id)["source"]


def add_source_version(source_id: str, content_text: str, version_label: str | None,
                       effective_from: str | None = None, effective_to: str | None = None) -> dict[str, Any]:
    digest = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
    path = _snapshot_path(source_id, digest)
    if not path.exists():
        path.write_text(content_text, encoding="utf-8")
    now = _now()
    with connection() as con:
        if not con.execute("SELECT 1 FROM sources WHERE source_id=?", (source_id,)).fetchone():
            raise KeyError("Source not found")
        existing = con.execute(
            "SELECT * FROM source_versions WHERE source_id=? AND content_hash_sha256=?",
            (source_id, digest)
        ).fetchone()
        if existing:
            return dict(existing)
        source_version_id = _id("SRCVER")
        con.execute(
            """INSERT INTO source_versions(source_version_id,source_id,version_label,content_hash_sha256,
               retrieved_at,effective_from,effective_to,local_snapshot_path)
               VALUES(?,?,?,?,?,?,?,?)""",
            (source_version_id, source_id, version_label, digest, now, effective_from,
             effective_to, str(path.relative_to(ROOT)))
        )
        con.commit()
        return dict(con.execute("SELECT * FROM source_versions WHERE source_version_id=?", (source_version_id,)).fetchone())


def record_health_check(source_id: str, check_status: str, http_status: int | None,
                        response_time_ms: int | None, content_hash_sha256: str | None,
                        notes: str | None) -> dict[str, Any]:
    if check_status not in {"HEALTHY","DEGRADED","UNREACHABLE","UNKNOWN"}:
        raise ValueError("Unsupported check status")
    check_id = _id("SRCCHECK")
    with connection() as con:
        if not con.execute("SELECT 1 FROM sources WHERE source_id=?", (source_id,)).fetchone():
            raise KeyError("Source not found")
        con.execute(
            "INSERT INTO source_health_checks VALUES(?,?,?,?,?,?,?,?)",
            (check_id, source_id, _now(), check_status, http_status, response_time_ms,
             content_hash_sha256, notes)
        )
        con.commit()
        return dict(con.execute("SELECT * FROM source_health_checks WHERE source_health_check_id=?", (check_id,)).fetchone())


def link_claim_evidence(claim_candidate_id: str, source_version_id: str,
                        evidence_relation: str, locator: str | None, excerpt: str | None,
                        linked_by: str) -> dict[str, Any]:
    if evidence_relation not in {"SUPPORTS","CONTRADICTS","CONTEXT"}:
        raise ValueError("Unsupported evidence relation")
    link_id = _id("CLMEV")
    with connection() as con:
        if not con.execute("SELECT 1 FROM claim_candidates WHERE claim_candidate_id=?", (claim_candidate_id,)).fetchone():
            raise KeyError("Claim candidate not found")
        if not con.execute("SELECT 1 FROM source_versions WHERE source_version_id=?", (source_version_id,)).fetchone():
            raise KeyError("Source version not found")
        existing = con.execute(
            """SELECT * FROM claim_source_evidence WHERE claim_candidate_id=? AND source_version_id=?
               AND evidence_relation=? AND COALESCE(locator,'')=COALESCE(?, '')""",
            (claim_candidate_id, source_version_id, evidence_relation, locator)
        ).fetchone()
        if existing:
            return dict(existing)
        con.execute(
            "INSERT INTO claim_source_evidence VALUES(?,?,?,?,?,?,?,?)",
            (link_id, claim_candidate_id, source_version_id, evidence_relation,
             locator, excerpt, linked_by, _now())
        )
        con.commit()
        return dict(con.execute("SELECT * FROM claim_source_evidence WHERE claim_source_evidence_id=?", (link_id,)).fetchone())


def compare_source_versions(source_id: str, left_id: str, right_id: str, compared_by: str) -> dict[str, Any]:
    with connection() as con:
        left = con.execute("SELECT * FROM source_versions WHERE source_version_id=? AND source_id=?", (left_id, source_id)).fetchone()
        right = con.execute("SELECT * FROM source_versions WHERE source_version_id=? AND source_id=?", (right_id, source_id)).fetchone()
        if not left or not right:
            raise KeyError("Source version not found")
        existing = con.execute(
            "SELECT * FROM source_version_comparisons WHERE left_source_version_id=? AND right_source_version_id=?",
            (left_id, right_id)
        ).fetchone()
        if existing:
            result = dict(existing)
            result["summary"] = json.loads(result.pop("summary_json"))
            return result
        def read_snapshot(row):
            rel = row["local_snapshot_path"]
            path = ROOT / rel if rel else None
            return path.read_text(encoding="utf-8") if path and path.exists() else ""
        left_text, right_text = read_snapshot(left), read_snapshot(right)
        diff = list(difflib.unified_diff(
            left_text.splitlines(), right_text.splitlines(),
            fromfile=left_id, tofile=right_id, lineterm=""
        ))
        summary = {
            "left_hash": left["content_hash_sha256"],
            "right_hash": right["content_hash_sha256"],
            "left_lines": len(left_text.splitlines()),
            "right_lines": len(right_text.splitlines()),
            "diff_lines": diff[:500],
            "diff_truncated": len(diff) > 500,
        }
        comparison_id = _id("SRCDIFF")
        changed = int(left["content_hash_sha256"] != right["content_hash_sha256"])
        con.execute(
            "INSERT INTO source_version_comparisons VALUES(?,?,?,?,?,?,?,?)",
            (comparison_id, source_id, left_id, right_id, changed,
             json.dumps(summary, sort_keys=True), compared_by, _now())
        )
        con.commit()
        return {
            "source_version_comparison_id": comparison_id,
            "source_id": source_id,
            "left_source_version_id": left_id,
            "right_source_version_id": right_id,
            "changed": changed,
            "summary": summary,
            "compared_by": compared_by,
        }
