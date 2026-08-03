# ADR-0004: Separate Creatures and Variants

- Status: Accepted
- Date: 2026-07-30

## Context
ARK contains base species and variants such as Alpha, Tek, Aberrant, X, and R forms. Treating every variant as an unrelated creature loses lineage and creates duplication.

## Decision
Base creatures and creature variants are separate entities connected by a required relationship.

## Consequences
Shared characteristics remain on the base creature. Variant-specific stats, drops, taming rules, and spawn data remain on the variant.
