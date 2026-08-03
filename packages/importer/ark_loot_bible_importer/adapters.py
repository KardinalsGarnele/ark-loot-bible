from __future__ import annotations
from abc import ABC, abstractmethod
import csv, json
from pathlib import Path
from typing import Any, Iterable

class AdapterError(ValueError):
    pass

class SourceAdapter(ABC):
    name: str
    @abstractmethod
    def read(self, path: Path) -> Iterable[dict[str, Any]]: ...
    @abstractmethod
    def validate(self, record: dict[str, Any], row_number: int) -> list[str]: ...

class CanonicalEntityCsvAdapter(SourceAdapter):
    name = "canonical-entity-csv-v1"
    required = {"entity_type", "external_key", "canonical_name"}
    def read(self, path: Path) -> Iterable[dict[str, Any]]:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            yield from csv.DictReader(handle)
    def validate(self, record: dict[str, Any], row_number: int) -> list[str]:
        missing = sorted(key for key in self.required if not str(record.get(key, "")).strip())
        return [f"row {row_number}: missing {key}" for key in missing]

class JsonLinesAdapter(SourceAdapter):
    name = "json-lines-v1"
    required = {"entity_type", "external_key", "canonical_name"}
    def read(self, path: Path) -> Iterable[dict[str, Any]]:
        with path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if line.strip():
                    try: yield json.loads(line)
                    except json.JSONDecodeError as exc: raise AdapterError(f"line {line_no}: {exc.msg}") from exc
    def validate(self, record: dict[str, Any], row_number: int) -> list[str]:
        missing = sorted(key for key in self.required if not str(record.get(key, "")).strip())
        return [f"row {row_number}: missing {key}" for key in missing]

ADAPTERS = {adapter.name: adapter for adapter in (CanonicalEntityCsvAdapter(), JsonLinesAdapter())}
