from fastapi.testclient import TestClient

from ark_loot_bible.main import app
from ark_loot_bible.content_pipeline import import_map_manifest
from ark_loot_bible.item_content import import_item_manifest
from ark_loot_bible.loot_content import import_loot_manifest
from ark_loot_bible.quality_engine import create_profile
from ark_loot_bible.loot_quality import configure_loot_source_quality, set_entry_item_multiplier, recalculate_loot_source_quality
from ark_loot_bible.loot_groups import configure_loot_source_group
from ark_loot_bible.config import ROOT

client = TestClient(app)

def prepare():
    import_map_manifest(ROOT/"imports/official/maps/the-island.manifest.json", commit=True)
    import_item_manifest(ROOT/"imports/official/items/rex-saddle.manifest.json", commit=True)
    import_loot_manifest(ROOT/"imports/official/loot/the-island-supply-reference.manifest.json", commit=True)
    create_profile("QUALITY-BPF-001", "BPF_200_250", "Blueprint Finder 200-250", 200, 250)
    configure_loot_source_quality("LOOTSOURCE-000001", "RED", True, 60, "QUALITY-BPF-001")
    configure_loot_source_group("LOOTSOURCE-000001", "SURFACE_SUPPLY", 10)
    set_entry_item_multiplier("LOOTENTRY-000001", 125)
    recalculate_loot_source_quality("LOOTSOURCE-000001")

def test_blueprint_finder_page():
    response = client.get("/blueprint-finder")
    assert response.status_code == 200
    assert "Wo droppt welches Blueprint?" in response.text

def test_search_returns_reverse_loot_path():
    prepare()
    response = client.get("/api/v1/blueprints", params={"q": "rex saddle"})
    assert response.status_code == 200
    data = response.json()
    assert data["result_count"] >= 1
    result = next(x for x in data["results"] if x["blueprint_id"] == "BP-000001")
    assert result["item_name"] == "Rex Saddle"
    assert result["source_count"] == 1
    path = result["loot_paths"][0]
    assert path["map_name"] == "The Island"
    assert path["source_group"] == "SURFACE_SUPPLY"
    assert path["drop_color"] == "RED"
    assert path["has_ring"] == 1
    assert path["calculated_quality_min_percent"] == 250.0
    assert path["calculated_quality_max_percent"] == 312.5

def test_combined_filters():
    prepare()
    yes = client.get("/api/v1/blueprints", params={
        "q": "rex", "map_id": "MAP-000001", "source_group": "SURFACE_SUPPLY",
        "drop_color": "RED", "has_ring": True, "required_level_max": 60
    }).json()
    no = client.get("/api/v1/blueprints", params={
        "q": "rex", "source_group": "CAVE"
    }).json()
    assert yes["result_count"] >= 1
    assert no["result_count"] == 0

def test_blueprint_profile_contains_locations_and_respawn_arrays():
    prepare()
    response = client.get("/api/v1/blueprints/BP-000001")
    assert response.status_code == 200
    data = response.json()
    assert "locations" in data
    assert "respawn_profiles" in data
    assert isinstance(data["locations"], list)
    assert isinstance(data["respawn_profiles"], list)

def test_unknown_blueprint_returns_404():
    assert client.get("/api/v1/blueprints/BP-999999").status_code == 404
