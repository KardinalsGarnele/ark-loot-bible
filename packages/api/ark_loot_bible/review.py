from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any
from .database import connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def create_review_case(import_record_id: str, priority: int = 50, assigned_to: str | None = None) -> dict[str, Any]:
    now = _now()
    with connection() as con:
        row = con.execute("SELECT * FROM import_records WHERE import_record_id=?", (import_record_id,)).fetchone()
        if not row:
            raise KeyError("Import record not found")
        existing = con.execute("SELECT review_case_id FROM review_cases WHERE import_record_id=?", (import_record_id,)).fetchone()
        if existing:
            return get_review_case(existing[0], con=con)
        case_id = _id("REVIEW")
        con.execute("""INSERT INTO review_cases(review_case_id,import_record_id,entity_type,proposed_entity_id,
            proposed_canonical_name,case_status,priority,assigned_to,opened_at,updated_at)
            VALUES(?,?,?,?,?,'OPEN',?,?,?,?)""",
            (case_id, import_record_id, row['entity_type'], row['proposed_entity_id'], row['proposed_canonical_name'], priority, assigned_to, now, now))
        _detect_conflicts(con, case_id, import_record_id)
        con.commit()
        return get_review_case(case_id, con=con)


def _detect_conflicts(con: sqlite3.Connection, case_id: str, import_record_id: str) -> None:
    claims = con.execute("SELECT claim_candidate_id,field_name,claim_value FROM claim_candidates WHERE import_record_id=?", (import_record_id,)).fetchall()
    by_field: dict[str, list[sqlite3.Row]] = {}
    for claim in claims:
        by_field.setdefault(claim['field_name'], []).append(claim)
    found = False
    for field, values in by_field.items():
        unique = {}
        for c in values:
            unique.setdefault(c['claim_value'], c)
        unique_values = list(unique.values())
        for i in range(len(unique_values)):
            for j in range(i + 1, len(unique_values)):
                found = True
                con.execute("""INSERT OR IGNORE INTO claim_conflicts(claim_conflict_id,review_case_id,field_name,
                    left_claim_candidate_id,right_claim_candidate_id) VALUES(?,?,?,?,?)""",
                    (_id("CONFLICT"), case_id, field, unique_values[i]['claim_candidate_id'], unique_values[j]['claim_candidate_id']))
    if found:
        con.execute("UPDATE review_cases SET case_status='CONFLICT',updated_at=? WHERE review_case_id=?", (_now(), case_id))


def list_review_cases(status: str | None = None, assigned_to: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    sql = "SELECT * FROM review_cases WHERE 1=1"
    params: list[Any] = []
    if status:
        sql += " AND case_status=?"; params.append(status)
    if assigned_to:
        sql += " AND assigned_to=?"; params.append(assigned_to)
    sql += " ORDER BY priority DESC, opened_at LIMIT ?"; params.append(limit)
    with connection() as con:
        return [dict(r) for r in con.execute(sql, params)]


def _read_review_case(con: sqlite3.Connection, review_case_id: str) -> dict[str, Any] | None:
    row = con.execute("SELECT * FROM review_cases WHERE review_case_id=?", (review_case_id,)).fetchone()
    if not row:
        return None
    out = dict(row)
    out['claims'] = [dict(r) for r in con.execute("""SELECT c.*,cr.decision AS review_decision,cr.normalized_value,cr.reviewer
        FROM claim_candidates c LEFT JOIN claim_reviews cr ON cr.claim_candidate_id=c.claim_candidate_id AND cr.review_case_id=?
        WHERE c.import_record_id=? ORDER BY c.field_name""", (review_case_id, row['import_record_id']))]
    out['conflicts'] = [dict(r) for r in con.execute("SELECT * FROM claim_conflicts WHERE review_case_id=?", (review_case_id,))]
    out['decisions'] = [dict(r) for r in con.execute("SELECT * FROM review_decisions WHERE review_case_id=? ORDER BY decided_at", (review_case_id,))]
    return out

def get_review_case(review_case_id: str, con: sqlite3.Connection | None = None) -> dict[str, Any] | None:
    if con is not None:
        return _read_review_case(con, review_case_id)
    with connection() as owned:
        return _read_review_case(owned, review_case_id)


def review_claim(review_case_id: str, claim_candidate_id: str, reviewer: str, decision: str,
                 normalized_value: str | None = None, notes: str | None = None) -> dict[str, Any]:
    if decision not in {'ACCEPT','REJECT','CONFLICT'}:
        raise ValueError('Invalid claim decision')
    with connection() as con:
        case = con.execute("SELECT * FROM review_cases WHERE review_case_id=?", (review_case_id,)).fetchone()
        if not case: raise KeyError('Review case not found')
        claim = con.execute("SELECT 1 FROM claim_candidates WHERE claim_candidate_id=? AND import_record_id=?", (claim_candidate_id, case['import_record_id'])).fetchone()
        if not claim: raise KeyError('Claim not found in review case')
        con.execute("""INSERT INTO claim_reviews(claim_review_id,review_case_id,claim_candidate_id,reviewer,decision,normalized_value,notes,reviewed_at)
            VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(review_case_id,claim_candidate_id,reviewer) DO UPDATE SET
            decision=excluded.decision,normalized_value=excluded.normalized_value,notes=excluded.notes,reviewed_at=excluded.reviewed_at""",
            (_id('CLAIMREVIEW'), review_case_id, claim_candidate_id, reviewer, decision, normalized_value, notes, _now()))
        con.execute("UPDATE review_cases SET case_status='IN_REVIEW',updated_at=?,row_version=row_version+1 WHERE review_case_id=?", (_now(), review_case_id))
        con.commit()
    return get_review_case(review_case_id)


def decide_case(review_case_id: str, reviewer: str, decision: str, notes: str | None = None) -> dict[str, Any]:
    mapping = {'APPROVE':'APPROVED','REJECT':'REJECTED','REQUEST_CHANGES':'IN_REVIEW','MARK_CONFLICT':'CONFLICT'}
    if decision not in mapping: raise ValueError('Invalid case decision')
    with connection() as con:
        case = con.execute("SELECT * FROM review_cases WHERE review_case_id=?", (review_case_id,)).fetchone()
        if not case: raise KeyError('Review case not found')
        if decision == 'APPROVE':
            unresolved = con.execute("SELECT COUNT(*) FROM claim_conflicts WHERE review_case_id=? AND conflict_status='OPEN'", (review_case_id,)).fetchone()[0]
            unreviewed = con.execute("""SELECT COUNT(*) FROM claim_candidates c LEFT JOIN claim_reviews r
              ON r.claim_candidate_id=c.claim_candidate_id AND r.review_case_id=?
              WHERE c.import_record_id=? AND (r.decision IS NULL OR r.decision!='ACCEPT')""", (review_case_id, case['import_record_id'])).fetchone()[0]
            if unresolved or unreviewed:
                raise ValueError('All claims must be accepted and conflicts resolved before approval')
        now=_now()
        con.execute("INSERT INTO review_decisions VALUES(?,?,?,?,?,?)", (_id('DECISION'),review_case_id,reviewer,decision,notes,now))
        closed = now if decision in {'APPROVE','REJECT'} else None
        con.execute("UPDATE review_cases SET case_status=?,updated_at=?,closed_at=?,row_version=row_version+1 WHERE review_case_id=?", (mapping[decision],now,closed,review_case_id))
        con.commit()
    return get_review_case(review_case_id)


def resolve_conflict(conflict_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    with connection() as con:
        row=con.execute("SELECT review_case_id FROM claim_conflicts WHERE claim_conflict_id=?",(conflict_id,)).fetchone()
        if not row: raise KeyError('Conflict not found')
        con.execute("UPDATE claim_conflicts SET conflict_status='RESOLVED',resolution_notes=?,resolved_by=?,resolved_at=? WHERE claim_conflict_id=?",(notes,reviewer,_now(),conflict_id))
        con.commit(); case_id=row[0]
    return get_review_case(case_id)
