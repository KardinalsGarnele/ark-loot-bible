# ADR-0008: API-first delivery

**Status:** Accepted  
**Date:** 2026-07-30

## Decision

The web interface, future bots, apps, and exports consume the same versioned application API. The first implementation uses FastAPI and SQLite, while domain rules remain independent from HTTP so storage and delivery technologies can evolve separately.

## Consequences

- No UI-only data model.
- Canonical records are queried through reusable repositories.
- OpenAPI becomes an executable contract.
- SQLite remains the local reference implementation; PostgreSQL can be introduced without changing public identifiers.
