import csv
import io
from fastapi.testclient import TestClient

from ark_loot_bible.main import app
from ark_loot_bible.content_pipeline import import_map_manifest
from ark_loot_bible.item_content import import_item_manifest
from ark_loot_bible.loot_content import import_loot_manifest
from ark_loot_bible.quality_engine import create_profile
from ark_loot_bible.loot_quality import configure_loot_source_quality, set_entry_item_multiplier, recalculate_loot_source_quality
from ark_loot_bible.config import ROOT

client = TestClient(app)

def prepare():
    import_map_manifest(ROOT/"imports/official/maps/the-island.manifest.json", commit=True)
    import_item_manifest(ROOT/"imports/official/items/rex-saddle.manifest.json", commit=True)
    import_loot_manifest(ROOT/"imports/official/loot/the-island-supply-reference.manifest.json", commit=True)
    create_profile("QUALITY-MATRIX-001", "MATRIX_200_250", "Matrix 200-250", 200, 250)
    configure_loot_source_quality("LOOTSOURCE-000001", "WHITE", True, 3, "QUALITY-MATRIX-001")
    set_entry_item_multiplier("LOOTENTRY-000001", 125)
    recalculate_loot_source_quality("LOOTSOURCE-000001")

def test_loot_matrix_page():
    response = client.get("/loot-matrix")
    assert response.status_code == 200
    assert "Map → Farbe → Ring" in response.text

def test_matrix_json_shape_and_filters():
    prepare()
    response = client.get("/api/v1/loot-matrix", params={
        "drop_color": "WHITE", "has_ring": True, "required_level_min": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] >= 1
    row = next(x for x in data["rows"] if x["loot_entry_id"] == "LOOTENTRY-000001")
    assert row["map_name"] == "The Island"
    assert row["drop_color"] == "WHITE"
    assert row["has_ring"] == 1
    assert row["required_level"] == 3
    assert row["calculated_quality_min_percent"] == 250.0
    assert row["calculated_quality_max_percent"] == 312.5

def test_csv_export_matches_matrix():
    prepare()
    response = client.get("/api/v1/loot-matrix/export.csv", params={"drop_color": "WHITE"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(response.text)))
    target = next(x for x in rows if x["loot_entry_name"] == "Rex Saddle Blueprint Reference Entry")
    assert target["drop_color"] == "WHITE"
    assert target["has_ring"] == "1"
    assert target["calculated_quality_max_percent"] == "312.5"

def test_json_export_matches_endpoint():
    prepare()
    direct = client.get("/api/v1/loot-matrix", params={"drop_color": "WHITE"}).json()
    exported = client.get("/api/v1/loot-matrix/export.json", params={"drop_color": "WHITE"}).json()
    assert direct["row_count"] == exported["row_count"]
    assert direct["rows"] == exported["rows"]

def test_ring_false_filter_excludes_ring_source():
    prepare()
    response = client.get("/api/v1/loot-matrix", params={"has_ring": False})
    assert all(row["loot_source_id"] != "LOOTSOURCE-000001" for row in response.json()["rows"])
