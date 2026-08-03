# Blueprint Finder

The Blueprint Finder reverses the normalized loot graph:

`Blueprint -> Loot Entry -> Loot Set -> Loot Source -> Map`

It exposes:

- item identity;
- source groups;
- drop color and ring;
- required level;
- source and effective quality ranges;
- locations;
- respawn profiles;
- verification status.

A structurally linked source is not automatically a verified gameplay claim.
The verification status remains visible at blueprint and loot-entry level.
