from fastapi.testclient import TestClient

from ark_loot_bible.main import app
from ark_loot_bible.content_pipeline import import_map_manifest
from ark_loot_bible.item_content import import_item_manifest
from ark_loot_bible.loot_content import import_loot_manifest
from ark_loot_bible.loot_groups import configure_loot_source_group, ensure_map_groups
from ark_loot_bible.config import ROOT

client = TestClient(app)

def prepare():
    import_map_manifest(ROOT/"imports/official/maps/the-island.manifest.json", commit=True)
    import_item_manifest(ROOT/"imports/official/items/rex-saddle.manifest.json", commit=True)
    import_loot_manifest(ROOT/"imports/official/loot/the-island-supply-reference.manifest.json", commit=True)

def test_all_map_groups_exist_even_when_empty():
    prepare()
    groups = ensure_map_groups("MAP-000001")
    assert len(groups) == 10
    assert {g["source_group"] for g in groups} >= {"SURFACE_SUPPLY","CAVE","DEEP_SEA","BOSS_TEK"}

def test_group_assignment_and_grouped_endpoint():
    prepare()
    value = configure_loot_source_group("LOOTSOURCE-000001", "SURFACE_SUPPLY", 10)
    assert value["source_group"] == "SURFACE_SUPPLY"
    response = client.get("/api/v1/maps/MAP-000001/loot-groups")
    assert response.status_code == 200
    data = response.json()
    surface = next(g for g in data["groups"] if g["source_group"] == "SURFACE_SUPPLY")
    cave = next(g for g in data["groups"] if g["source_group"] == "CAVE")
    assert surface["loot_source_count"] >= 1
    assert cave["loot_source_count"] == 0

def test_matrix_source_group_filter():
    prepare()
    configure_loot_source_group("LOOTSOURCE-000001", "SURFACE_SUPPLY", 10)
    yes = client.get("/api/v1/loot-matrix", params={"source_group":"SURFACE_SUPPLY"}).json()
    no = client.get("/api/v1/loot-matrix", params={"source_group":"CAVE"}).json()
    assert yes["row_count"] >= 1
    assert no["row_count"] == 0

def test_invalid_group_rejected():
    prepare()
    response = client.put("/api/v1/loot-sources/LOOTSOURCE-000001/group", json={
        "source_group": "SPACE_LOOT", "display_order": 1
    })
    assert response.status_code == 422

def test_group_page_filter_present():
    response = client.get("/loot-matrix")
    assert response.status_code == 200
    assert "Cave Loot" in response.text
    assert "Deep Sea" in response.text
