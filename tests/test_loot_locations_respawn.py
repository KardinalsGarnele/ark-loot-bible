from fastapi.testclient import TestClient

from ark_loot_bible.main import app
from ark_loot_bible.content_pipeline import import_map_manifest
from ark_loot_bible.item_content import import_item_manifest
from ark_loot_bible.loot_content import import_loot_manifest
from ark_loot_bible.config import ROOT

client = TestClient(app)

def prepare():
    import_map_manifest(ROOT/"imports/official/maps/the-island.manifest.json", commit=True)
    import_item_manifest(ROOT/"imports/official/items/rex-saddle.manifest.json", commit=True)
    import_loot_manifest(ROOT/"imports/official/loot/the-island-supply-reference.manifest.json", commit=True)

def test_region_location_and_respawn_round_trip():
    prepare()
    region = client.post("/api/v1/map-regions", json={
        "map_id": "MAP-000001",
        "display_name": "Demonstration Region",
        "geometry_type": "AREA_LABEL"
    })
    assert region.status_code == 200
    region_id = region.json()["map_region_id"]

    location = client.post("/api/v1/loot-sources/LOOTSOURCE-000001/locations", json={
        "location_type": "REGION",
        "map_region_id": region_id,
        "coordinate_precision": "REGION_ONLY"
    })
    assert location.status_code == 200

    respawn = client.put("/api/v1/loot-sources/LOOTSOURCE-000001/respawn", json={
        "respawn_mode": "UNKNOWN"
    })
    assert respawn.status_code == 200

    profile = client.get("/api/v1/loot-sources/LOOTSOURCE-000001/location-profile")
    assert profile.status_code == 200
    assert len(profile.json()["locations"]) >= 1
    assert profile.json()["respawn"]["respawn_mode"] == "UNKNOWN"

def test_fixed_point_requires_coordinates():
    prepare()
    response = client.post("/api/v1/loot-sources/LOOTSOURCE-000001/locations", json={
        "location_type": "FIXED_POINT",
        "latitude": 50
    })
    assert response.status_code == 422

def test_coordinates_must_be_map_range():
    prepare()
    response = client.post("/api/v1/loot-sources/LOOTSOURCE-000001/locations", json={
        "location_type": "FIXED_POINT",
        "latitude": 101,
        "longitude": 50,
        "coordinate_precision": "EXACT"
    })
    assert response.status_code == 422

def test_respawn_range_validation():
    prepare()
    response = client.put("/api/v1/loot-sources/LOOTSOURCE-000001/respawn", json={
        "respawn_mode": "RANGE",
        "minimum_seconds": 600,
        "maximum_seconds": 300
    })
    assert response.status_code == 422

def test_unknown_values_are_allowed():
    prepare()
    response = client.put("/api/v1/loot-sources/LOOTSOURCE-000001/respawn", json={
        "respawn_mode": "UNKNOWN",
        "minimum_seconds": None,
        "maximum_seconds": None,
        "requires_pickup": None
    })
    assert response.status_code == 200
    data = response.json()
    assert data["minimum_seconds"] is None
    assert data["maximum_seconds"] is None
