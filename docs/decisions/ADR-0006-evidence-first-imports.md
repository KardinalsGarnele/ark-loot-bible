# ADR-0006: Evidence-First Imports

- **Status:** Accepted
- **Decision date:** 2026-07-30

## Context

Direct imports into canonical tables make it easy for parsing errors, uncertain claims, or changing source pages to become published facts.

## Decision

All external data enters a staging layer. Each import is tied to a hashed source version. Records and field-level claims are validated independently. Uncertain data is quarantined. Canonical promotion requires an explicit reviewable action.

## Consequences

- Imports are reproducible and auditable.
- Raw source payloads are preserved.
- Canonical tables stay clean.
- Importing is slower than direct insertion, but correction costs and trust risks are substantially lower.
