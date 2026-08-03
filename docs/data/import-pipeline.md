# Canonical Import Pipeline

The pipeline is intentionally non-destructive and evidence-first.

```text
Source
→ Source Version
→ Import Batch
→ Import Record
→ Claim Candidate
→ Validation
→ Quarantine or Promotion
→ Canonical Entity
→ Evidence Attachment
```

## Staging

`tools/stage_claims.py` reads a claim CSV and stores the raw payload. It does not create canonical entities.

## Validation

A record can be syntactically valid while one or more claims remain quarantined. Every claim needs an assessed evidence strength.

## Promotion

`tools/promote_import.py` promotes only a record whose record and all claim candidates are `VALID`. Promotion creates a stable entity ID but leaves the entity at `NEEDS_VERIFICATION` until field-level evidence has been attached and reviewed.

## Reproducibility

Every batch points to an exact source version and SHA-256 content hash. The original staged payload remains preserved after promotion.
