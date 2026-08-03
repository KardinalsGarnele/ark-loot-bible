from fastapi.testclient import TestClient
from ark_loot_bible.main import app
from ark_loot_bible.config import ROOT
from ark_loot_bible.content_pipeline import import_map_manifest
client=TestClient(app)
MANIFEST=ROOT/"imports/official/maps/the-island.manifest.json"
def test_manifest_dry_run():
 r=import_map_manifest(MANIFEST,commit=False);assert r["status"]=="VALIDATED";assert r["records_valid"]==9;assert r["preview"]["map_id"]=="MAP-000001"
def test_manifest_commit_and_idempotency():
 first=import_map_manifest(MANIFEST,commit=True,actor="test");assert first["status"] in {"COMPLETED","NO_CHANGES"};second=import_map_manifest(MANIFEST,commit=True,actor="test");assert second["status"]=="NO_CHANGES"
def test_map_content_endpoint():
 import_map_manifest(MANIFEST,commit=True,actor="test");response=client.get("/api/v1/maps/MAP-000001/content");assert response.status_code==200;body=response.json();assert body["map"]["canonical_name"]=="The Island";assert len(body["components"])==8;assert all(x["component_status"]=="EMPTY" for x in body["components"]);assert len(body["evidence"])>=5
def test_content_manifest_api():
 response=client.get("/api/v1/content-manifests");assert response.status_code==200;assert isinstance(response.json(),list)
