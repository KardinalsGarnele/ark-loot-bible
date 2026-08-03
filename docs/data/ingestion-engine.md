# Ingestion Engine

Sprint 010 introduces adapter-based, evidence-first ingestion.

## Safety boundaries

- Dry-run is the default.
- Commit mode stages validated raw records; it never promotes canonical facts.
- Content hashes make successful committed inputs idempotent.
- Any invalid record aborts a committed batch atomically.
- Every run and validation message is auditable.

## CLI

```bash
python tools/ingest.py imports/samples/entities.csv
python tools/ingest.py imports/samples/entities.csv --commit
```

Adapters implement `read()` and `validate()`. Included adapters support canonical-entity CSV and JSON Lines.
