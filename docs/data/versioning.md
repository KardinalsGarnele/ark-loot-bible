# Data Versioning

## Principles

- Schema and data releases are versioned independently.
- Historical values are preserved with validity intervals.
- Imports are reproducible and record their source snapshot.
- Exports include database version, schema version, generated timestamp, and source coverage.

## Change categories

- `ADDED`
- `UPDATED`
- `DEPRECATED`
- `REMOVED_FROM_GAME`
- `VERIFICATION_CHANGED`
- `SOURCE_CHANGED`
