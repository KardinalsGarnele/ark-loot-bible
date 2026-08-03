from fastapi.testclient import TestClient
from ark_loot_bible.main import app

client=TestClient(app)

def test_loot_sources_list():
    r=client.get('/api/v1/loot-sources')
    assert r.status_code==200
    assert r.json() == []

def test_loot_source_graph():
    r=client.get('/api/v1/loot-sources/LOOTSOURCE-000001')
    assert r.status_code==200
    body=r.json()
    assert body['sets'][0]['entries'][0]['blueprint_id']=='BP-000001'
    assert body['sets'][0]['entries'][0]['entry_weight'] is None

def test_item_loot_paths():
    r=client.get('/api/v1/items/ITEM-000001/loot-paths')
    assert r.status_code==200
    assert r.json()[0]['loot_source_id']=='LOOTSOURCE-000001'

def test_loot_source_404():
    assert client.get('/api/v1/loot-sources/LOOTSOURCE-999999').status_code==404
