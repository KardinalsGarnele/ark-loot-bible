from pathlib import Path
import os, sqlite3, sys
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/generated/ark_loot_bible.sqlite'
os.environ['ARK_LOOT_BIBLE_DB']=str(DB)
sys.path.insert(0,str(ROOT/'packages/api'))
from fastapi.testclient import TestClient
from ark_loot_bible.main import app


def seed_case(case_suffix: str, entity_type: str, entity_id: str, claims: dict[str,str]):
    con=sqlite3.connect(DB); con.execute('PRAGMA foreign_keys=ON')
    sid=f'SRC-PROMO-{case_suffix}'; sv=f'SRCVER-PROMO-{case_suffix}'; batch=f'BATCH-PROMO-{case_suffix}'; rec=f'RECORD-PROMO-{case_suffix}'; case=f'REVIEW-PROMO-{case_suffix}'
    con.execute("INSERT OR IGNORE INTO sources(source_id,source_type,title,locator,publisher,captured_at,notes) VALUES(?,?,?,?,?,?,?)",(sid,'TEST','Promotion source','local://promotion','ARK Loot Bible','2026-07-31T00:00:00Z','test'))
    con.execute("INSERT OR IGNORE INTO source_versions(source_version_id,source_id,content_hash_sha256,retrieved_at) VALUES(?,?,?,?)",(sv,sid,f'hash-{case_suffix}','2026-07-31T00:00:00Z'))
    con.execute("INSERT OR IGNORE INTO import_batches(import_batch_id,source_version_id,importer_name,importer_version,started_at,batch_status,record_count) VALUES(?,?,?,?,?,'VALIDATED',1)",(batch,sv,'test','1','2026-07-31T00:00:00Z'))
    con.execute("INSERT OR IGNORE INTO import_records(import_record_id,import_batch_id,source_row_key,entity_type,proposed_entity_id,proposed_canonical_name,payload_json,record_status,created_at) VALUES(?,?,?,?,?,?,?,'VALID',?)",(rec,batch,'1',entity_type,entity_id,claims['canonical_name'],'{}','2026-07-31T00:00:00Z'))
    con.execute("INSERT OR IGNORE INTO review_cases(review_case_id,import_record_id,entity_type,proposed_entity_id,proposed_canonical_name,case_status,priority,opened_at,updated_at) VALUES(?,?,?,?,?,'APPROVED',50,?,?)",(case,rec,entity_type,entity_id,claims['canonical_name'],'2026-07-31T00:00:00Z','2026-07-31T00:00:00Z'))
    for i,(field,value) in enumerate(claims.items()):
        cid=f'CLAIM-PROMO-{case_suffix}-{i}'
        con.execute("INSERT OR IGNORE INTO claim_candidates(claim_candidate_id,import_record_id,field_name,claim_value,evidence_strength,proposed_verification_status,candidate_status) VALUES(?,?,?,?,?,'VERIFIED','VALID')",(cid,rec,field,str(value),'PRIMARY'))
        con.execute("INSERT OR IGNORE INTO claim_reviews(claim_review_id,review_case_id,claim_candidate_id,reviewer,decision,reviewed_at) VALUES(?,?,?,?, 'ACCEPT', ?)",(f'CR-PROMO-{case_suffix}-{i}',case,cid,'tester','2026-07-31T00:00:00Z'))
    con.commit(); con.close(); return case


def test_item_preview_and_atomic_promotion():
    case=seed_case('ITEM','ITEM','ITEM-900001',{'canonical_name':'Promotion Test Saddle','game_title':'ARK: Survival Ascended','category_code':'SADDLE','quality_capable':'true','stack_size':'1'})
    client=TestClient(app)
    preview=client.get(f'/api/v1/promotions/{case}/preview').json()
    assert preview['status']=='READY' and preview['operation']=='CREATE'
    commit=client.post(f'/api/v1/promotions/{case}?actor=tester').json()
    assert commit['status']=='PROMOTED' and commit['revision_number']==1
    detail=client.get('/api/v1/items/ITEM-900001')
    assert detail.status_code==200 and detail.json()['canonical_name']=='Promotion Test Saddle'
    again=client.post(f'/api/v1/promotions/{case}?actor=tester').json()
    assert again['status']=='ALREADY_PROMOTED'


def test_creature_promotion_and_revision_endpoint():
    case=seed_case('CREATURE','CREATURE','CREATURE-900001',{'canonical_name':'Promotion Test Creature','game_title':'ARK: Survival Ascended','species_name':'Testus canonicalis','tameable':'false','breedable':'false'})
    client=TestClient(app)
    assert client.post(f'/api/v1/promotions/{case}?actor=tester').status_code==200
    creature=client.get('/api/v1/creatures/CREATURE-900001')
    assert creature.status_code==200 and creature.json()['species_name']=='Testus canonicalis'
    revisions=client.get('/api/v1/entities/CREATURE-900001/revisions').json()
    assert len(revisions)==1 and revisions[0]['operation']=='CREATE'


def test_invalid_item_category_rolls_back_everything():
    case=seed_case('BADCAT','ITEM','ITEM-900002',{'canonical_name':'Bad Category Item','game_title':'ARK: Survival Ascended','category_code':'DOES_NOT_EXIST'})
    client=TestClient(app)
    response=client.post(f'/api/v1/promotions/{case}?actor=tester')
    assert response.status_code==409
    con=sqlite3.connect(DB)
    assert con.execute("SELECT COUNT(*) FROM entities WHERE entity_id='ITEM-900002'").fetchone()[0]==0
    assert con.execute("SELECT COUNT(*) FROM canonical_revisions WHERE review_case_id=?",(case,)).fetchone()[0]==0
    con.close()
