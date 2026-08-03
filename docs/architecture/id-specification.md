# Stable ID Specification

## Format

`<PREFIX>-<6 DIGIT SEQUENCE>`

Examples:

- `MAP-000001`
- `CREATURE-000001`
- `CVAR-000001`
- `SPAWN-000001`
- `ITEM-000001`
- `BP-000001`
- `ENGRAM-000001`
- `LSRC-000001`
- `LSET-000001`
- `LENT-000001`
- `BOSS-000001`
- `TEK-000001`
- `DOSSIER-000001`
- `NOTE-000001`
- `SRC-000001`
- `EVID-000001`

## Rules

1. IDs are immutable.
2. IDs are never reused.
3. Deleted or deprecated entities retain their IDs.
4. Display names and slugs may change without changing the ID.
5. Foreign keys always use stable IDs.
6. Import pipelines may stage external keys but must resolve them to stable IDs before canonical publication.
