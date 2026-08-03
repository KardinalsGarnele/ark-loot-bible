from fastapi.testclient import TestClient
from ark_loot_bible.main import app

client = TestClient(app)

def test_admin_console_is_served():
    r = client.get('/admin')
    assert r.status_code == 200
    assert 'Data Steward Console' in r.text


def test_admin_summary_shape():
    r = client.get('/api/v1/admin/summary')
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {'imports','reviews','canonical','quality_gate'}
    assert 'open' in body['reviews']
    assert 'revisions' in body['canonical']


def test_admin_imports_endpoint():
    r = client.get('/api/v1/admin/imports')
    assert r.status_code == 200
    assert isinstance(r.json(), list)
