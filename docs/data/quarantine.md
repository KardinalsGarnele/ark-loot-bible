# Data Quarantine

Quarantine is a normal workflow state, not a failure.

Records or claims are quarantined when they are incomplete, contradictory, unassessed, malformed, or not yet traceable to adequate evidence.

Canonical tables must never be used as a holding area for uncertain data.

## Common reason codes

- `UNASSESSED_EVIDENCE`
- `UNKNOWN_ENTITY_TYPE`
- `MISSING_CANONICAL_NAME`
- `CONFLICTING_SOURCES`
- `INVALID_IDENTIFIER`
- `BROKEN_RELATIONSHIP`

A quarantined record remains immutable as imported. Resolution is recorded separately so the audit trail is preserved.
