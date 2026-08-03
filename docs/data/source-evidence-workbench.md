# Source & Evidence Workbench

The workbench manages source identity, immutable snapshots, health checks,
version comparisons and field-level evidence links to staged claims.

A source version is content-addressed by SHA-256. Re-importing the same content
returns the existing version instead of creating a duplicate.

Claim evidence links may SUPPORT, CONTRADICT or provide CONTEXT. They do not
approve a claim by themselves; the human review gate remains mandatory.
