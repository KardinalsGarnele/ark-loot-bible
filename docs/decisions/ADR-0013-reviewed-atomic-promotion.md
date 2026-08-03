# ADR-0013: Reviewed Atomic Promotion

## Status
Accepted.

## Decision
Only an `APPROVED` review case may be promoted. Promotion is entity-specific,
transactional, evidence-linked, revisioned and idempotent.

A preview produces a field-level diff. Commit optionally checks the review
case row version to prevent stale approvals from being promoted.

## Consequences
- Partial canonical writes are rolled back.
- Every successful promotion creates an immutable revision snapshot.
- The same review case cannot create two revisions.
- Unknown fields or invalid reference values block promotion.
