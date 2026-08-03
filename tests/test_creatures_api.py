from fastapi.testclient import TestClient
from ark_loot_bible.main import app

client = TestClient(app)

def test_list_creatures_contains_reference_rex():
    response = client.get('/api/v1/creatures?q=rex')
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]['creature_id'] == 'CREATURE-000001'
    assert rows[0]['verification_status'] == 'NEEDS_VERIFICATION'

def test_creature_detail_has_default_variant():
    response = client.get('/api/v1/creatures/CREATURE-000001')
    assert response.status_code == 200
    body = response.json()
    assert body['canonical_name'] == 'Rex'
    assert body['variants'][0]['variant_id'] == 'VARIANT-000001'
    assert body['variants'][0]['is_default'] == 1
    assert body['maps'] == []

def test_creature_not_found():
    response = client.get('/api/v1/creatures/CREATURE-999999')
    assert response.status_code == 404
