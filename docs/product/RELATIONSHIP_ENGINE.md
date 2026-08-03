# Relationship Engine

Sprint 008 introduces a unified read graph and global search.

## Search

`GET /api/v1/search?q=rex`

Only verified entities are returned by default. Development and unverified records require `include_unverified=true`.

## Graph

`GET /api/v1/graph/{entity_id}?depth=2`

Depth is limited to 1–3. The response contains a root node, deduplicated nodes and typed edges. Each edge exposes its authoritative source table.

## Current adapters

- generic entity relationships
- item relationships
- creature relationships
- blueprints
- loot sources, sets and entries

The graph is a read model. Canonical facts continue to live in normalized domain tables.
