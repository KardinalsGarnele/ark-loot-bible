# Loot Domain Model

The loot graph is normalized as `LootSource -> LootSet -> LootEntry -> Item/Blueprint`.

Numeric gameplay fields are nullable. Missing evidence must remain `NULL`; zero is a real value and may not be used as a placeholder.

Every layer is an entity with a stable ID and independent verification status. This allows sources, sets, and individual entries to be revised without changing public identifiers.
