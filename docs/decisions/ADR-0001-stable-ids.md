# ADR-0001: Use Stable Internal IDs

- Status: Accepted
- Date: 2026-07-30

## Context
Names, localizations, categories, and slugs can change. Relationships and public references must remain stable.

## Decision
Every canonical entity receives an immutable internal ID with a registered prefix and six-digit sequence.

## Consequences
Relationships, exports, URLs, and external integrations remain stable across renames and revisions. IDs cannot be recycled.
