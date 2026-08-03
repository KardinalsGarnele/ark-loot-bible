# ADR-0014: Progressive Data Steward Console

Status: Accepted

## Decision

Human data operations use one focused review workspace. The interface reveals import context, claims, conflicts, promotion differences, and revisions progressively. Canonical writes remain exclusively owned by the atomic promotion service.

## Consequences

- The UI cannot bypass review or promotion guards.
- Operational complexity remains available without overwhelming reviewers.
- Every visible action maps to an auditable API operation.
