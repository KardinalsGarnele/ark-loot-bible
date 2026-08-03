# Canonical Map Policy 1.0

A map may be promoted only when its import record is valid, every claim has assessed evidence, a stable `MAP-` ID is supplied, and the identity fields are complete. Promotion is atomic: entity, map subtype, evidence, field links, audit log, and scope linkage are committed together or not at all.

Required identity fields: `canonical_name`, `game_title`, `map_kind`, `included_with_base_game`, and `official`.
