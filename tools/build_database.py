#!/usr/bin/env python3
"""Build a clean SQLite database from ordered schema and migrations."""
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "database" / "generated" / "ark_loot_bible.sqlite"
SQL_FILES = [
    ROOT / "database/schema/core.sql",
    ROOT / "database/migrations/0002_registry_relationships_spawns.sql",
    ROOT / "database/migrations/0003_source_registry_import_pipeline.sql",
    ROOT / "database/migrations/0004_canonical_maps.sql",
    ROOT / "database/migrations/0005_canonical_items.sql",
    ROOT / "database/migrations/0006_canonical_creatures.sql",
    ROOT / "database/migrations/0007_loot_domain.sql",
    ROOT / "database/migrations/0008_ingestion_engine.sql",
    ROOT / "database/migrations/0009_review_promotion_workflow.sql",
    ROOT / "database/migrations/0010_canonical_promotion_revisions.sql",
    ROOT / "database/migrations/0011_source_evidence_workbench.sql",
    ROOT / "database/migrations/0012_official_content_pipeline.sql",
    ROOT / "database/migrations/0013_creature_content_pipeline.sql",
    ROOT / "database/migrations/0014_item_blueprint_content_pipeline.sql",
    ROOT / "database/migrations/0015_loot_content_pipeline.sql",
    ROOT / "database/migrations/0016_quality_profile_engine.sql",
    ROOT / "database/migrations/0017_loot_quality_integration.sql",
    ROOT / "database/migrations/0018_loot_source_groups.sql",
    ROOT / "database/migrations/0019_loot_locations_respawn.sql",
]

def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()
    con = sqlite3.connect(OUTPUT)
    try:
        for path in SQL_FILES:
            con.executescript(path.read_text(encoding="utf-8"))
        con.executescript((ROOT / "database/seeds/item-categories.sql").read_text(encoding="utf-8"))
        con.executescript((ROOT / "database/seeds/creature-reference.sql").read_text(encoding="utf-8"))
        con.executescript((ROOT / "database/seeds/loot-reference.sql").read_text(encoding="utf-8"))
        violations = con.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations: {violations}")
        con.commit()
    finally:
        con.close()
    print(OUTPUT.relative_to(ROOT))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
