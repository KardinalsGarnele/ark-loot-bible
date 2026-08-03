# ADR-0009: Null Before Guessing

## Status
Accepted

## Decision
Unknown loot weights, roll counts, quantities, blueprint chances, and quality ranges are stored as `NULL`.

## Consequence
The API can expose a verified structural relationship without implying unsupported probabilities or values.
