# ADR-0010: Unified Read Graph

## Status
Accepted

## Decision
The public graph API is a read model assembled from normalized domain tables. Domain data remains in its authoritative tables; it is not copied into a second canonical graph store.

## Consequences
- Domain constraints remain explicit.
- New entity families can add graph adapters without rewriting existing data.
- Every returned edge identifies its source table.
- Verification state remains visible on nodes and edges.
