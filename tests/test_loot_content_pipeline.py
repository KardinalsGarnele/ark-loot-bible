from fastapi.testclient import TestClient
from ark_loot_bible.main import app
from ark_loot_bible.loot_content import import_loot_manifest
from ark_loot_bible.item_content import import_item_manifest
from ark_loot_bible.content_pipeline import import_map_manifest
from ark_loot_bible.config import ROOT

client=TestClient(app)
loot_manifest=ROOT/"imports/official/loot/the-island-supply-reference.manifest.json"

def prepare():
    import_map_manifest(ROOT/"imports/official/maps/the-island.manifest.json",commit=True)
    import_item_manifest(ROOT/"imports/official/items/rex-saddle.manifest.json",commit=True)

def test_loot_manifest_dry_run():
    r=import_loot_manifest(loot_manifest,commit=False)
    assert r["status"]=="VALIDATED"
    assert r["records_seen"]==11

def test_loot_manifest_commit_and_idempotency():
    prepare()
    first=import_loot_manifest(loot_manifest,commit=True)
    assert first["status"] in {"COMPLETED","NO_CHANGES"}
    second=import_loot_manifest(loot_manifest,commit=True)
    assert second["status"]=="NO_CHANGES"

def test_loot_content_api():
    prepare(); import_loot_manifest(loot_manifest,commit=True)
    r=client.get("/api/v1/loot-sources/LOOTSOURCE-000001/content")
    assert r.status_code==200
    data=r.json()
    assert len(data["components"])==8
    assert len(data["sets"])==1
    entry=data["sets"][0]["entries"][0]
    assert entry["blueprint_chance"] is None
    assert entry["effective_quality_min"] is None
    assert entry["effective_quality_max"] is None

def test_loot_content_missing():
    assert client.get("/api/v1/loot-sources/LOOTSOURCE-999999/content").status_code==404
