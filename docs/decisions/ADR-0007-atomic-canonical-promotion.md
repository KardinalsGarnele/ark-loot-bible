# ADR-0007: Atomic canonical promotion

## Status
Accepted

## Decision
Canonical subtype promotion must create the base entity, subtype row, field evidence, audit record, and scope link in one database transaction.

## Consequence
A failed import cannot leave partially canonical records behind.
