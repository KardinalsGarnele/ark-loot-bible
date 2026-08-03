from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json, sqlite3, uuid
from pathlib import Path
from .adapters import ADAPTERS, SourceAdapter

@dataclass(frozen=True)
class IngestionResult:
    run_id: str; status: str; mode: str; records_seen: int; records_accepted: int; records_rejected: int; input_sha256: str
    def to_dict(self): return asdict(self)

class IngestionEngine:
    def __init__(self, database: Path): self.database = Path(database)
    @staticmethod
    def sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
    def run(self, input_path: Path, adapter_name: str, *, commit: bool=False) -> IngestionResult:
        path=Path(input_path); adapter: SourceAdapter=ADAPTERS[adapter_name]; digest=self.sha256(path); mode='COMMIT' if commit else 'DRY_RUN'
        con=sqlite3.connect(self.database); con.execute('PRAGMA foreign_keys=ON'); run_id=f"INGEST-{uuid.uuid4().hex[:12].upper()}"
        duplicate=con.execute("SELECT run_id FROM ingestion_runs WHERE adapter_name=? AND input_sha256=? AND mode='COMMIT' AND status IN ('COMPLETED','NO_CHANGES')",(adapter_name,digest)).fetchone() if commit else None
        if duplicate:
            con.execute("INSERT INTO ingestion_runs(run_id,adapter_name,input_uri,input_sha256,mode,status,completed_at) VALUES(?,?,?,?,?,'NO_CHANGES',CURRENT_TIMESTAMP)",(run_id,adapter_name,str(path),digest,mode)); con.commit(); con.close()
            return IngestionResult(run_id,'NO_CHANGES',mode,0,0,0,digest)
        con.execute("INSERT INTO ingestion_runs(run_id,adapter_name,input_uri,input_sha256,mode,status) VALUES(?,?,?,?,?,'STARTED')",(run_id,adapter_name,str(path),digest,mode))
        seen=accepted=rejected=0
        try:
            for seen, record in enumerate(adapter.read(path),1):
                errors=adapter.validate(record,seen)
                if errors:
                    rejected+=1
                    for message in errors: con.execute("INSERT INTO ingestion_messages(run_id,record_key,severity,code,message) VALUES(?,?, 'ERROR','VALIDATION_ERROR',?)",(run_id,record.get('external_key'),message))
                    continue
                accepted+=1
                if commit:
                    payload=json.dumps(record,ensure_ascii=False,sort_keys=True)
                    con.execute("INSERT INTO import_records(import_record_id,import_batch_id,source_row_key,entity_type,proposed_canonical_name,payload_json,record_status,created_at) VALUES(?,?,?,?,?,?,'VALID',CURRENT_TIMESTAMP)",
                      (f"IREC-{uuid.uuid4().hex[:12].upper()}", self._batch(con,run_id,adapter_name,digest,path), record['external_key'], record['entity_type'], record['canonical_name'], payload))
            status='COMPLETED' if rejected==0 else 'FAILED'
            con.execute("UPDATE ingestion_runs SET status=?,records_seen=?,records_accepted=?,records_rejected=?,completed_at=CURRENT_TIMESTAMP WHERE run_id=?",(status,seen,accepted,rejected,run_id))
            if commit and rejected: con.rollback(); raise ValueError(f"validation failed for {rejected} record(s)")
            con.commit(); return IngestionResult(run_id,status,mode,seen,accepted,rejected,digest)
        except Exception as exc:
            con.rollback(); con.execute("UPDATE ingestion_runs SET status='FAILED',error_message=?,records_seen=?,records_accepted=?,records_rejected=?,completed_at=CURRENT_TIMESTAMP WHERE run_id=?",(str(exc),seen,accepted,rejected,run_id)); con.commit(); raise
        finally: con.close()
    @staticmethod
    def _batch(con, run_id, adapter_name, digest, path):
        batch=f"BATCH-{run_id[7:]}"; row=con.execute("SELECT 1 FROM import_batches WHERE import_batch_id=?",(batch,)).fetchone()
        if not row:
            source=con.execute("SELECT source_version_id FROM source_versions ORDER BY retrieved_at LIMIT 1").fetchone()
            if not source: raise RuntimeError('at least one registered source version is required for commit mode')
            con.execute("INSERT INTO import_batches(import_batch_id,source_version_id,importer_name,importer_version,started_at,batch_status,record_count,notes) VALUES(?,?,?,?,CURRENT_TIMESTAMP,'VALIDATED',0,?)",(batch,source[0],adapter_name,'1.0',str(path)))
        return batch
