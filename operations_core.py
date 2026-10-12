"""Durable operator incident cases from POSITIVE signed Perpl evidence.

Production goal: real venue status -> case -> scoped human decision ->
read-only recheck -> evidence-backed outcome. NO exchange trade/cancel POST
and no claim that resolving an operator review fixes an exchange order.

This store deliberately shares the IncidentStore SQLite connection with the
signed observations to avoid a parallel demonstration-only product.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def compact(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)

ACTIONS={"ACKNOWLEDGE","HOLD","ESCALATE","REQUEST_RECHECK","CLOSE_REVIEW"}
STATUS={"OPEN","ACKNOWLEDGED","HELD","ESCALATED","RECHECK_REQUESTED","REVIEW_CLOSED"}
def _ints(x):
    return type(x) is int and x>=0

class CaseNotFound(KeyError):pass
class CaseConflict(ValueError):pass
class CaseForbidden(ValueError):pass

class OperatorCases:
    def __init__(self,incident_store):
        self.store=incident_store
        self.db=incident_store.db
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS operator_cases(
          id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE,
          account_id INTEGER NOT NULL, market_id INTEGER NOT NULL,
          request_id INTEGER NOT NULL, order_id INTEGER,
          kind TEXT NOT NULL, severity TEXT NOT NULL, state TEXT NOT NULL,
          version INTEGER NOT NULL, source TEXT NOT NULL,
          first_evidence_sha TEXT NOT NULL, latest_evidence_sha TEXT NOT NULL,
          first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL,
          last_review_at TEXT, actor_name TEXT, latest_evidence_json TEXT NOT NULL,
          last_venue_verdict TEXT NOT NULL DEFAULT 'NOT_RECONCILED',
          incident_recovery_proven INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS operator_case_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          case_id TEXT NOT NULL REFERENCES operator_cases(id),
          kind TEXT NOT NULL, actor TEXT NOT NULL, source TEXT NOT NULL,
          idempotency_key TEXT,
          payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
          prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
          created_at TEXT NOT NULL, UNIQUE(case_id,idempotency_key)
        );
        CREATE INDEX IF NOT EXISTS case_events_by_case ON operator_case_events(case_id,id);
        """)
    def _fingerprint(self,incident):
        # Reject automatic case opening from manual fixtures or any unsigned
        # account claim. The caller is the server-signed snapshot workflow.
        parts=("testnet",str(incident["account_id"]),str(incident["market_id"]),
               str(incident["original_request_id"]),str(incident.get("order_id")),
               str(incident["kind"]))
        return hashlib.sha256("|".join(parts).encode()).hexdigest()
    def _event(self,case_id,kind,actor,source,payload,idempotency_key=None):
        previous=self.db.execute(
          "SELECT event_hash FROM operator_case_events WHERE case_id=? ORDER BY id DESC LIMIT 1",
          (case_id,)).fetchone()
        prev=previous["event_hash"] if previous else "GENESIS"
        data=compact(payload); sha=hashlib.sha256(data.encode()).hexdigest(); ts=utc_now()
        fingerprint=hashlib.sha256(
            f"{case_id}\n{kind}\n{actor}\n{source}\n{sha}\n{prev}\n{ts}".encode()).hexdigest()
        self.db.execute("""INSERT INTO operator_case_events(
            case_id,kind,actor,source,idempotency_key,payload_json,payload_sha256,
            prev_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (case_id,kind,actor,source,idempotency_key,data,sha,prev,fingerprint,ts))
    def ingest_verified(self,observation,observation_sha):
        """Called only after validated signed snapshot persistence. Fail closed.

        Never creates a case from a normal OPEN/CANCELED order or fw=false.
        """
        if (not isinstance(observation,dict)
            or observation.get("classification")!="AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW"
            or observation.get("source")!="SIGNED_PERPL_HTTP_GET"
            or observation.get("chain_id")!=10143):
            raise ValueError("signed Perpl Testnet origin required")
        if not isinstance(observation_sha,str) or len(observation_sha)!=64:
            raise ValueError("signed account evidence digest required")
        original=self.store.latest_account_observation()
        if hashlib.sha256(compact(original).encode()).hexdigest()!=observation_sha:
            raise ValueError("signed account evidence not in local observation ledger")
        reviews=observation.get("negative_path_review",{})
        if reviews.get("classification")!="SIGNED_PERPL_NEGATIVE_PATH_REVIEW":
            raise ValueError("negative-path review is not source-bound")
        owned={x.get("account_id") for x in observation.get("accounts",[])
               if isinstance(x,dict) and _ints(x.get("account_id"))}
        created=0; touched=0
        for case in reviews.get("cases",[]):
            if not isinstance(case,dict) or case.get("kind") not in (
                "POSITIVE_EXCHANGE_FAILURE_EVENT","UNRESOLVED_ORDER_OUTCOME"):
                raise ValueError("non-positive case attempted")
            a=case.get("account_id");m=case.get("market_id");r=case.get("original_request_id")
            if a not in owned or not all(_ints(v) for v in (a,m,r)):
                raise ValueError("order outside signed account scope")
            oid=case.get("order_id")
            if oid is not None and not _ints(oid):
                raise ValueError("malformed oid")
            if case["kind"]=="POSITIVE_EXCHANGE_FAILURE_EVENT":
                # All failed cases must be grounded in a valid, signed first-page
                # FAILED (st=7) observation for the same account/market/rq/oid.
                history=observation.get("observed_orders",{}).get("history_page_1",{}).get("rows",[])
                if not any(e.get("source")=="AUTHENTICATED_HISTORY_FIRST_PAGE" and
                   e.get("status_code")==7 and e.get("account_id")==a and
                   e.get("market_id")==m and e.get("request_id")==r and
                   e.get("order_id")==oid for e in history):
                    raise ValueError("positive exchange failure not in signed history")
            else:
                changes=observation.get("order_lifecycle",{}).get("transitions",[])
                if not any(t.get("finding") in (
                    "DISAPPEARED_OUTCOME_UNKNOWN","CONFLICTING_TERMINAL_HISTORY_REVIEW")
                    and t.get("account_id")==a and t.get("market_id")==m
                    and t.get("request_id")==r and t.get("order_id")==oid for t in changes):
                    raise ValueError("UNKNOWN case not found in signed comparison")
            fp=self._fingerprint(case)
            sanitized={
                "kind":case["kind"],"severity":case["severity"],"interpretation":case["interpretation"],
                "next_step":case["next_step"],"source":case["evidence"],
                "status_reason_code":case.get("status_reason_code"),
                "failure_reason_code":case.get("failure_reason_code"),
                "retries_authorized":False,"exchange_writes_enabled":False}
            ts=utc_now()
            row=self.db.execute("SELECT id,state FROM operator_cases WHERE fingerprint=?",(fp,)).fetchone()
            if row is not None:
                self.db.execute("""UPDATE operator_cases SET last_seen_at=?,
                  latest_evidence_sha=?, latest_evidence_json=? WHERE id=?""",
                  (ts,observation_sha,compact(sanitized),row["id"]))
                touched+=1
                continue
            ident=str(uuid.uuid4())
            self.db.execute("""INSERT INTO operator_cases(
              id,fingerprint,account_id,market_id,request_id,order_id,kind,severity,state,version,
              source,first_evidence_sha,latest_evidence_sha,first_seen_at,last_seen_at,
              latest_evidence_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (ident,fp,a,m,r,oid,case["kind"],case["severity"],"OPEN",1,
               case["evidence"],observation_sha,observation_sha,ts,ts,compact(sanitized)))
            self._event(ident,"CASE_CREATED","SYSTEM_SIGNED_READ",case["evidence"],{
                "scope":[a,m,r,oid],"kind":case["kind"],
                "observation_sha256":observation_sha,"verdict":"REVIEW_ONLY_NO_EXCHANGE_ACTION"})
            created+=1
        return {"created":created,"updated":touched,"source":"PERSISTED_SIGNED_READ",
                "exchange_writes_enabled":False}
    def list(self,limit=100):
        if type(limit) is not int or not 1<=limit<=200:
            raise ValueError("invalid case list limit")
        rows=self.db.execute(
            "SELECT id FROM operator_cases ORDER BY last_seen_at DESC,id DESC LIMIT ?",(limit,)
        ).fetchall()
        return [self.get(row["id"]) for row in rows]
    def get(self,ident):
        row=self.db.execute("SELECT * FROM operator_cases WHERE id=?",(ident,)).fetchone()
        if not row:raise CaseNotFound(ident)
        result=dict(row)
        result["latest_evidence"]=json.loads(result.pop("latest_evidence_json"))
        result["incident_recovery_proven"]=False
        result["exchange_writes_enabled"]=False
        result["next_actions"]=[
            {"action":action,"exchange_write":False} for action in sorted(ACTIONS)]
        return result
    def events(self,ident):
        self.get(ident)
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM operator_case_events WHERE case_id=? ORDER BY id",(ident,)).fetchall()]
    def verify(self,ident):
        previous="GENESIS"
        for e in self.events(ident):
            ph=hashlib.sha256(e["payload_json"].encode()).hexdigest()
            if ph!=e["payload_sha256"] or e["prev_hash"]!=previous:return False
            digest=hashlib.sha256(
                f"{ident}\n{e['kind']}\n{e['actor']}\n{e['source']}\n{ph}\n{previous}\n{e['created_at']}".encode()).hexdigest()
            if digest!=e["event_hash"]:return False
            previous=e["event_hash"]
        return True
    def decide(self,ident,action,actor,note,expected_version,idempotency_key):
        if action not in ACTIONS:raise CaseForbidden("unsupported local operator decision")
        if not isinstance(actor,str) or not (3<=len(actor.strip())<=80):
            raise CaseForbidden("operator identity required")
        if not isinstance(note,str) or not (12<=len(note.strip())<=1000):
            raise CaseForbidden("reason must be 12-1000 characters")
        if type(expected_version) is not int or expected_version<1:
            raise CaseForbidden("explicit optimistic version required")
        if not isinstance(idempotency_key,str) or not (12<=len(idempotency_key)<=128) or not all(c.isalnum() or c in "-_" for c in idempotency_key):
            raise CaseForbidden("valid unique operator request id required")
        statuses={"ACKNOWLEDGE":"ACKNOWLEDGED","HOLD":"HELD","ESCALATE":"ESCALATED",
                  "REQUEST_RECHECK":"RECHECK_REQUESTED","CLOSE_REVIEW":"REVIEW_CLOSED"}
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing=self.db.execute(
                "SELECT kind,payload_json FROM operator_case_events WHERE case_id=? AND idempotency_key=?",
                (ident,idempotency_key)).fetchone()
            if existing:
                payload=json.loads(existing["payload_json"])
                if payload.get("action")!=action or payload.get("actor")!=actor.strip() or payload.get("note")!=note.strip():
                    raise CaseConflict("idempotency request reused with different intent")
                self.db.execute("COMMIT")
                return {**self.get(ident),"idempotent_replay":True}
            row=self.db.execute("SELECT * FROM operator_cases WHERE id=?",(ident,)).fetchone()
            if not row:raise CaseNotFound(ident)
            if row["version"]!=expected_version:
                raise CaseConflict("stale operator view; refresh before deciding")
            if row["state"]=="REVIEW_CLOSED" and action!="ESCALATE":
                raise CaseForbidden("closed case requires explicit escalation to reopen")
            if action=="CLOSE_REVIEW":
                if row["kind"]!="POSITIVE_EXCHANGE_FAILURE_EVENT" or row["source"]!="PERPL_SIGNED_FIRST_HISTORY_PAGE":
                    raise CaseForbidden("UNKNOWN cannot be closed as resolved; obtain positive final exchange evidence")
            state=statuses[action]
            self.db.execute("""UPDATE operator_cases SET state=?,version=?,actor_name=?,
                 last_review_at=? WHERE id=?""",
                 (state,row["version"]+1,actor.strip(),utc_now(),ident))
            self._event(ident,"OPERATOR_"+action,actor.strip(),"LOCAL_OPERATOR_ACTION",
                {"action":action,"actor":actor.strip(),"note":note.strip(),
                 "expected_version":expected_version,"exchange_writes":False,
                 "incident_recovery_proven":False,
                 "meaning":"REVIEW_CLOSED_IS_NOT_VENUE_RECOVERED" if action=="CLOSE_REVIEW"
                 else "LOCAL_OPERATOR_DECISION_NOT_EXCHANGE_ACTION"},idempotency_key)
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        return {**self.get(ident),"idempotent_replay":False}
