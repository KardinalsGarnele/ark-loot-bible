# ADR-0003: Relationships Over Duplication

- Status: Accepted
- Date: 2026-07-30

## Context
Duplicated names and attributes create contradictions and expensive maintenance.

## Decision
Facts are normalized and connected through explicit relationships.

## Consequences
Queries may require joins, but updates occur in one place and all interfaces remain consistent.
