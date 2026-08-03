# Loot Quality Integration

Loot sources can now carry:

- drop color;
- ring variant;
- required player level;
- quality profile.

Loot entries carry their item-specific quality multiplier separately from the
calculated result.

Formula:

`source quality × (item quality multiplier / 100) × profile multipliers`

Demonstration only:

- source range: 200–250%;
- item multiplier: 125%;
- calculated result: 250–312.5%.

The demonstration profile is `NEEDS_VERIFICATION` and must not be interpreted as
a factual claim about a real crate.
