# Loot Matrix

The Loot Matrix is the first player-facing table generated entirely from the
canonical data model.

Default sort order:

1. map;
2. drop color;
3. ring variant;
4. required level;
5. loot source;
6. loot set;
7. loot entry.

The browser view and CSV/JSON exports use the same query service, preventing
different outputs from drifting apart.

Unknown values are rendered as empty or `—`; they are never replaced with
guesses.
