from fastapi.testclient import TestClient
from ark_loot_bible.main import app
client=TestClient(app)
def test_coverage_page(): assert client.get("/coverage").status_code==200
def test_global_coverage_shape():
    d=client.get("/api/v1/coverage").json()
    assert "totals" in d and "sections" in d
    assert 0 <= d["totals"]["VERIFIED_PERCENT"] <= 100
def test_gap_list():
    r=client.get("/api/v1/coverage/gaps?limit=5")
    assert r.status_code==200 and len(r.json())<=5
def test_map_coverage():
    r=client.get("/api/v1/maps/MAP-000001/coverage")
    assert r.status_code==200
    assert "loot_groups" in r.json()
def test_unknown_map_coverage_404():
    assert client.get("/api/v1/maps/MAP-999999/coverage").status_code==404
