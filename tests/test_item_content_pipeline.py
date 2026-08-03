from fastapi.testclient import TestClient
from ark_loot_bible.main import app
from ark_loot_bible.item_content import import_item_manifest
from ark_loot_bible.config import ROOT

client=TestClient(app)
manifest=ROOT/"imports/official/items/rex-saddle.manifest.json"

def test_item_manifest_dry_run():
    r=import_item_manifest(manifest,commit=False)
    assert r["status"]=="VALIDATED"
    assert r["records_seen"]==10

def test_item_manifest_commit_and_idempotency():
    first=import_item_manifest(manifest,commit=True)
    assert first["status"] in {"COMPLETED","NO_CHANGES"}
    second=import_item_manifest(manifest,commit=True)
    assert second["status"]=="NO_CHANGES"

def test_item_content_api():
    import_item_manifest(manifest,commit=True)
    r=client.get("/api/v1/items/ITEM-000001/content")
    assert r.status_code==200
    data=r.json()
    assert data["item"]["entity_id"]=="ITEM-000001"
    assert len(data["blueprints"])>=1
    assert len(data["components"])==8

def test_item_content_missing():
    assert client.get("/api/v1/items/ITEM-999999/content").status_code==404
