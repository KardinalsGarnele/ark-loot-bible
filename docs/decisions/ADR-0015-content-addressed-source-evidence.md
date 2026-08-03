# ADR-0015: Content-addressed source evidence

## Status
Accepted.

## Decision
Every source snapshot is identified by its SHA-256 content hash. Claim evidence
references an immutable source version, never only a mutable URL.

## Consequences
- identical snapshots are idempotent;
- source changes are diffable;
- evidence remains reproducible when websites change;
- source health is tracked separately from factual verification.
