# ADR-0011: Adapter-based ingestion

**Status:** Accepted

Source formats are isolated behind adapters. The ingestion engine owns hashing, validation, idempotency, audit records and atomic staging. Adapters may parse source-specific structures, but they may not write canonical tables or bypass verification.
