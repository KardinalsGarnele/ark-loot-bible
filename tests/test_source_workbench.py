from fastapi.testclient import TestClient
from ark_loot_bible.main import app
from ark_loot_bible.database import connection

client=TestClient(app)

def test_source_console_served():
    r=client.get("/admin/sources")
    assert r.status_code==200
    assert "Source & Evidence Workbench" in r.text

def test_source_crud_version_health_and_compare():
    sid="SRC-TEST-014"
    r=client.post("/api/v1/sources",json={
        "source_id":sid,"source_type":"OFFICIAL_WIKI","title":"Test source",
        "locator":"https://example.invalid/test","publisher":"Test","notes":"test"
    })
    assert r.status_code==200
    v1=client.post(f"/api/v1/sources/{sid}/versions",json={"content_text":"alpha\\nbeta","version_label":"1"}).json()
    v1_repeat=client.post(f"/api/v1/sources/{sid}/versions",json={"content_text":"alpha\\nbeta","version_label":"1"}).json()
    assert v1_repeat["source_version_id"]==v1["source_version_id"]
    v2=client.post(f"/api/v1/sources/{sid}/versions",json={"content_text":"alpha\\ngamma","version_label":"2"}).json()
    h=client.post(f"/api/v1/sources/{sid}/health-checks",json={"check_status":"HEALTHY","http_status":200,"response_time_ms":42})
    assert h.status_code==200
    c=client.get(f"/api/v1/sources/{sid}/compare",params={"left":v1["source_version_id"],"right":v2["source_version_id"]})
    assert c.status_code==200
    assert c.json()["changed"]==1
    w=client.get(f"/api/v1/sources/{sid}")
    assert w.status_code==200
    assert len(w.json()["versions"])==2

def test_claim_evidence_link():
    with connection() as con:
        claim=con.execute("SELECT claim_candidate_id FROM claim_candidates LIMIT 1").fetchone()
        version=con.execute("SELECT source_version_id FROM source_versions LIMIT 1").fetchone()
    if claim and version:
        r=client.post(f"/api/v1/claims/{claim[0]}/evidence",json={
            "source_version_id":version[0],"evidence_relation":"SUPPORTS",
            "locator":"row 1","excerpt":"evidence","linked_by":"test"
        })
        assert r.status_code==200

def test_source_list_shape():
    r=client.get("/api/v1/sources")
    assert r.status_code==200
    assert isinstance(r.json(),list)
