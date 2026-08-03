from fastapi.testclient import TestClient
from ark_loot_bible.main import app
from ark_loot_bible.quality_engine import calculate_quality_range
client=TestClient(app)

def test_requested_example():
    x=calculate_quality_range(200,250,125)
    assert x["result_min_percent"]==250.0
    assert x["result_max_percent"]==312.5

def test_100_to_100():
    x=calculate_quality_range(100,100,125)
    assert x["result_min_percent"]==125.0
    assert x["result_max_percent"]==125.0

def test_incomplete_values_remain_null():
    x=calculate_quality_range(None,250,125)
    assert x["status"]=="INCOMPLETE"
    assert x["result_min_percent"] is None

def test_api_calculator():
    r=client.post("/api/v1/quality/calculate",json={
      "source_quality_min_percent":200,"source_quality_max_percent":250,
      "item_quality_multiplier_percent":125})
    assert r.status_code==200
    assert r.json()["result_max_percent"]==312.5

def test_profile_round_trip():
    r=client.post("/api/v1/quality-profiles",json={
      "quality_profile_id":"QUALITY-TEST-001","profile_code":"TEST_200_250",
      "display_name":"Test 200-250","source_quality_min_percent":200,
      "source_quality_max_percent":250})
    assert r.status_code==200
    r=client.post("/api/v1/quality-profiles/QUALITY-TEST-001/calculate",json={
      "item_quality_multiplier_percent":125})
    assert r.status_code==200
    assert r.json()["result_min_percent"]==250.0
