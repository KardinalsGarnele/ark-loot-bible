from fastapi.testclient import TestClient
from ark_loot_bible.main import app

client = TestClient(app)

def test_global_search_hides_unverified_by_default():
    r = client.get('/api/v1/search', params={'q':'rex'})
    assert r.status_code == 200
    assert r.json() == []

def test_global_search_can_include_development_records():
    r = client.get('/api/v1/search', params={'q':'rex','include_unverified':'true'})
    assert r.status_code == 200
    ids = {x['entity_id'] for x in r.json()}
    assert 'CREATURE-000001' in ids
    assert 'ITEM-000001' in ids
    assert all(x['path'].startswith('/api/v1/') for x in r.json())

def test_graph_traverses_rex_saddle_path():
    r = client.get('/api/v1/graph/ITEM-000001', params={'depth':3})
    assert r.status_code == 200
    data = r.json()
    ids = {n['entity_id'] for n in data['nodes']}
    assert {'ITEM-000001','CREATURE-000001','BP-000001','LOOTENTRY-000001','LOOTSET-000001','LOOTSOURCE-000001'} <= ids
    types = {e['edge_type'] for e in data['edges']}
    assert {'USED_BY_CREATURE','BLUEPRINT_OF','REWARDS_ITEM','CONTAINS_LOOT_ENTRY','CONTAINS_LOOT_SET'} <= types

def test_graph_unknown_entity_is_404():
    assert client.get('/api/v1/graph/ITEM-999999').status_code == 404

def test_search_requires_query():
    assert client.get('/api/v1/search').status_code == 422
