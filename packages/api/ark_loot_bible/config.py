from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[3]

@dataclass(frozen=True)
class Settings:
    database_path: Path = Path(os.getenv("ARK_LOOT_BIBLE_DB", ROOT / "database/generated/ark_loot_bible.sqlite"))
    app_name: str = "ARK Loot Bible API"
    app_version: str = "0.26.0"

settings = Settings()
