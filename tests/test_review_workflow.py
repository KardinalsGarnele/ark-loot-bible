from pathlib import Path
import os, sqlite3, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/generated/ark_loot_bible.sqlite'
os.environ['ARK_LOOT_BIBLE_DB']=str(DB)
sys.path.insert(0,str(ROOT/'packages/api'))
from fastapi.testclient import TestClient
from ark_loot_bible.main import app


def seed_review_record():
    con=sqlite3.connect(DB)
    con.execute('PRAGMA foreign_keys=ON')
    con.execute("INSERT OR IGNORE INTO sources(source_id,source_type,title,locator,publisher,captured_at,notes) VALUES('SRC-REVIEW','TEST','Review source','local://review','ARK Loot Bible','2026-07-30T00:00:00Z','test')")
    con.execute("INSERT OR IGNORE INTO source_versions(source_version_id,source_id,content_hash_sha256,retrieved_at) VALUES('SRCVER-REVIEW','SRC-REVIEW','abc123','2026-07-30T00:00:00Z')")
    con.execute("INSERT OR IGNORE INTO import_batches(import_batch_id,source_version_id,importer_name,importer_version,started_at,batch_status,record_count) VALUES('BATCH-REVIEW','SRCVER-REVIEW','test','1','2026-07-30T00:00:00Z','VALIDATED',1)")
    con.execute("INSERT OR IGNORE INTO import_records(import_record_id,import_batch_id,source_row_key,entity_type,proposed_entity_id,proposed_canonical_name,payload_json,record_status,created_at) VALUES('RECORD-REVIEW','BATCH-REVIEW','1','ITEM','ITEM-999999','Test Item','{}','VALID','2026-07-30T00:00:00Z')")
    con.execute("INSERT OR IGNORE INTO claim_candidates(claim_candidate_id,import_record_id,field_name,claim_value,evidence_strength,proposed_verification_status,candidate_status) VALUES('CLAIM-A','RECORD-REVIEW','canonical_name','Test Item','PRIMARY','VERIFIED','VALID')")
    con.execute("INSERT OR IGNORE INTO claim_candidates(claim_candidate_id,import_record_id,field_name,claim_value,evidence_strength,proposed_verification_status,candidate_status) VALUES('CLAIM-B','RECORD-REVIEW','game_title','ARK: Survival Ascended','PRIMARY','VERIFIED','VALID')")
    con.commit(); con.close()


def test_review_case_requires_all_claims():
    seed_review_record(); client=TestClient(app)
    r=client.post('/api/v1/reviews/import-records/RECORD-REVIEW?priority=80&assigned_to=alice')
    assert r.status_code==200
    case=r.json(); assert case['priority']==80 and len(case['claims'])==2
    case_id=case['review_case_id']
    blocked=client.post(f'/api/v1/reviews/{case_id}/decision?reviewer=alice&decision=APPROVE')
    assert blocked.status_code==409
    for claim in case['claims']:
        ok=client.post(f"/api/v1/reviews/{case_id}/claims/{claim['claim_candidate_id']}?reviewer=alice&decision=ACCEPT")
        assert ok.status_code==200
    approved=client.post(f'/api/v1/reviews/{case_id}/decision?reviewer=alice&decision=APPROVE')
    assert approved.status_code==200
    assert approved.json()['case_status']=='APPROVED'


def test_review_open_is_idempotent():
    seed_review_record(); client=TestClient(app)
    a=client.post('/api/v1/reviews/import-records/RECORD-REVIEW').json()
    b=client.post('/api/v1/reviews/import-records/RECORD-REVIEW').json()
    assert a['review_case_id']==b['review_case_id']
