from pathlib import Path
from fastapi.testclient import TestClient
from ark_loot_bible.main import app
from ark_loot_bible.creature_content import import_creature_manifest
from ark_loot_bible.config import ROOT
client=TestClient(app)
MANIFEST=ROOT/"imports/reference/creatures/rex.manifest.json"
def test_dry_run():
 r=import_creature_manifest(MANIFEST,commit=False);assert r["status"]=="VALIDATED";assert r["records_valid"]==12
def test_commit_and_idempotency():
 r=import_creature_manifest(MANIFEST,commit=True);assert r["status"] in {"COMPLETED","NO_CHANGES"}
 r2=import_creature_manifest(MANIFEST,commit=True);assert r2["status"]=="NO_CHANGES"
def test_content_api():
 import_creature_manifest(MANIFEST,commit=True)
 r=client.get("/api/v1/creatures/CREATURE-000001/content");assert r.status_code==200;d=r.json();assert d["creature"]["canonical_name"]=="Rex";assert len(d["components"])==10
def test_no_gameplay_claims():
 import_creature_manifest(MANIFEST,commit=True);d=client.get("/api/v1/creatures/CREATURE-000001/content").json();assert d["creature"]["tameable"] is None;assert d["creature"]["breedable"] is None
