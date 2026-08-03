from fastapi.testclient import TestClient
from ark_loot_bible.main import app
from ark_loot_bible.content_pipeline import import_map_manifest
from ark_loot_bible.item_content import import_item_manifest
from ark_loot_bible.loot_content import import_loot_manifest
from ark_loot_bible.quality_engine import create_profile
from ark_loot_bible.loot_quality import (
    configure_loot_source_quality,
    set_entry_item_multiplier,
    recalculate_loot_source_quality,
)
from ark_loot_bible.config import ROOT

client = TestClient(app)

def prepare():
    import_map_manifest(ROOT/"imports/official/maps/the-island.manifest.json", commit=True)
    import_item_manifest(ROOT/"imports/official/items/rex-saddle.manifest.json", commit=True)
    import_loot_manifest(ROOT/"imports/official/loot/the-island-supply-reference.manifest.json", commit=True)
    create_profile(
        "QUALITY-DEMO-200-250", "DEMO_200_250", "Demonstration 200-250%",
        200, 250, verification_status="NEEDS_VERIFICATION"
    )

def test_loot_quality_calculation():
    prepare()
    configure_loot_source_quality("LOOTSOURCE-000001", "RED", True, 60, "QUALITY-DEMO-200-250")
    set_entry_item_multiplier("LOOTENTRY-000001", 125)
    result = recalculate_loot_source_quality("LOOTSOURCE-000001")
    assert result["entries_calculated"] == 1
    assert result["results"][0]["result_min_percent"] == 250.0
    assert result["results"][0]["result_max_percent"] == 312.5

def test_missing_multiplier_stays_incomplete():
    prepare()
    configure_loot_source_quality("LOOTSOURCE-000001", "RED", False, 60, "QUALITY-DEMO-200-250")
    set_entry_item_multiplier("LOOTENTRY-000001", None)
    result = recalculate_loot_source_quality("LOOTSOURCE-000001")
    assert result["entries_incomplete"] == 1
    assert result["results"][0]["result_min_percent"] is None

def test_quality_api_round_trip():
    prepare()
    r = client.put("/api/v1/loot-sources/LOOTSOURCE-000001/quality", json={
        "drop_color": "red", "has_ring": True, "required_level": 60,
        "quality_profile_id": "QUALITY-DEMO-200-250"
    })
    assert r.status_code == 200
    r = client.put("/api/v1/loot-entries/LOOTENTRY-000001/quality-multiplier", json={
        "item_quality_multiplier_percent": 125
    })
    assert r.status_code == 200
    r = client.post("/api/v1/loot-sources/LOOTSOURCE-000001/quality/recalculate", json={})
    assert r.status_code == 200
    assert r.json()["results"][0]["result_max_percent"] == 312.5

def test_quality_matrix_filter():
    prepare()
    configure_loot_source_quality("LOOTSOURCE-000001", "WHITE", True, 3, "QUALITY-DEMO-200-250")
    r = client.get("/api/v1/loot-quality", params={"drop_color": "WHITE", "has_ring": True})
    assert r.status_code == 200
    assert any(row["loot_source_id"] == "LOOTSOURCE-000001" for row in r.json())

def test_invalid_color_rejected():
    prepare()
    r = client.put("/api/v1/loot-sources/LOOTSOURCE-000001/quality", json={
        "drop_color": "pink", "has_ring": False, "required_level": 3,
        "quality_profile_id": "QUALITY-DEMO-200-250"
    })
    assert r.status_code == 422
