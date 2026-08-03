# Review and Promotion Workflow

Staged records become review cases. Reviewers evaluate every field-level claim, resolve conflicts, and make an auditable case decision. Approval is blocked until every claim is accepted and every detected conflict is resolved. Approval does not itself write canonical data; entity-specific promoters remain the only canonical write boundary.

States: `OPEN → IN_REVIEW → APPROVED/REJECTED`, with `CONFLICT` used while incompatible claims remain unresolved.
