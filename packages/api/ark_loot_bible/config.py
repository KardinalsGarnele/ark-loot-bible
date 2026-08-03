
from dataclasses import dataclass
from pathlib import Path
import os


ROOT = Path(
    os.getenv("ARK_LOOT_BIBLE_ROOT", Path.cwd())
).resolve()


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path(
        os.getenv(
            "ARK_LOOT_BIBLE_DB",
            ROOT / "database/generated/ark_loot_bible.sqlite",
        )
    )
    app_name: str = "ARK Loot Bible API"
    app_version: str = "0.26.1"


settings = Settings()