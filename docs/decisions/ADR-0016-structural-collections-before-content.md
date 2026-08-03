# ADR-0016: Structural collections before child content

## Status
Accepted.

## Decision
A map may expose typed empty collections before the collection members are known. The collection relationship is verified as platform structure; gameplay members remain unpublished until their own evidence-backed import succeeds.

## Consequences
- the frontend can render a stable information architecture;
- empty collections cannot be mistaken for complete datasets;
- child imports can progress independently.
