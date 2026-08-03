# Quality Profile & Blueprint Range Engine

Formula version 1.0:

`effective quality = source quality percent × (item quality multiplier percent / 100) × additional multiplier`

Example:

- source range: 200–250%
- item quality multiplier: 125%
- result: 250–312.5%

The engine does not infer missing values. Incomplete inputs produce null results.
Difficulty and crate multipliers are optional profile fields and default to 1 only
when a profile calculation is explicitly requested.
