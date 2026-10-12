"""End-to-end tests for real core product state, not static evidence artifacts."""
import importlib
import json
import sqlite3
import uuid
import pytest
from fastapi.testclient import TestClient
from incident_core import IncidentStore
from operations_core import OperatorCases,CaseConflict,CaseForbidden

def signed_raw(history=(),opens=(),history_more=False):
    return {
     "wallet":{"mt":19,"sn":400,"as":[
      {"id":1060,"in":1,"fw":False,"fr":False,"lfr":1800000000000}]},
     "orders":{"mt":23,"sn":401,"d":list(opens)},
     "positions":{"mt":26,"sn":402,"d":[]},
     "order_history":{"d":list(history),"np":"other-cursor" if history_more else ""},
     "fills":{"d":[],"np":""},
    }

FAILED={"acc":1060,"mkt":16,"rq":50,"oid":0,"st":7,"sr":34}
OPEN={"acc":1060,"mkt":16,"rq":51,"oid":1234,"st":2}

@pytest.fixture
def harness(monkeypatch,tmp_path):
    app_module=importlib.import_module("app")
    path=str(tmp_path/"operations.sqlite3")
    app_module.store=IncidentStore(path)
    local=TestClient(app_module.app)
    observations=[signed_raw(history=[FAILED])]
    class FakeSignedRead:
        @classmethod
        def from_env(cls,network):
            assert network=="testnet"
            return cls()
        def read_all(self):
            return observations.pop(0)
    monkeypatch.setattr(app_module,"PerplReadClient",FakeSignedRead)
    yield app_module,local,observations,path
    app_module.store.db.close()

def session(client):
    result=client.get("/api/ops/session")
    assert result.status_code==200
    return {"X-Operator-Session":result.json()["operator_session"]}

def refresh(client):
    result=client.post("/api/account/live-refresh")
    assert result.status_code==200,result.text
    return result.json()

def cases(client):
    result=client.get("/api/ops/cases")
    assert result.status_code==200
    return result.json()["items"]

def decision(client,item,action="ACKNOWLEDGE",headers=None,idem=None,reason=None,actor="Local operator"):
    return client.post("/api/ops/cases/"+item["id"]+"/decision",
        json={"action":action,"actor":actor,
              "reason":reason or "Compte verifie, ne jamais soumettre un doublon.",
              "expected_version":item["version"],
              "idempotency_key":idem or str(uuid.uuid4())},
        headers=headers or {})

def test_confirmed_signed_failure_creates_one_real_persisted_case(harness):
    app,client,reads,path=harness
    result=refresh(client)
    assert result["operator_case_ingest"]["created"]==1
    c=cases(client)[0]
    assert c["account_id"]==1060 and c["request_id"]==50
    assert c["kind"]=="POSITIVE_EXCHANGE_FAILURE_EVENT"
    assert c["source"]=="PERPL_SIGNED_FIRST_HISTORY_PAGE"
    assert c["latest_evidence"]["status_reason_code"]==34
    assert c["order_id"] is None
    assert c["state"]=="OPEN" and c["incident_recovery_proven"] is False
    assert app.case_manager().verify(c["id"])
    assert client.get("/api/ops/cases/"+c["id"]+"/ledger").json()["hash_chain_valid"]
    assert client.get("/api/incidents").json()["items"]==[]

def test_no_duplicate_case_on_repeat_signed_read(harness):
    app,client,reads,path=harness
    refresh(client)
    reads.append(signed_raw(history=[FAILED]))
    result=refresh(client)
    assert result["operator_case_ingest"]=={
        "created":0,"updated":1,"source":"PERSISTED_SIGNED_READ",
        "exchange_writes_enabled":False}
    assert len(cases(client))==1
    c=cases(client)[0]
    assert len(app.case_manager().events(c["id"]))==1

def test_normal_order_or_normal_cancel_never_creates_incident(harness):
    app,client,reads,path=harness
    reads.clear()
    reads.extend([
       signed_raw(opens=[OPEN],history=[OPEN]),
       signed_raw(history=[{**OPEN,"rq":99,"st":5},{**OPEN,"st":2}])
    ])
    refresh(client);assert cases(client)==[]
    refresh(client);assert cases(client)==[]

def test_local_ack_is_real_persistent_mutation_not_exchange_write(harness):
    app,client,reads,path=harness
    refresh(client)
    c=cases(client)[0]
    res=decision(client,c,headers=session(client))
    assert res.status_code==200,res.text
    new=res.json()
    assert new["state"]=="ACKNOWLEDGED" and new["version"]==2
    assert not new["exchange_writes_enabled"]
    assert new["incident_recovery_proven"] is False
    assert app.case_manager().verify(c["id"])
    newstore=IncidentStore(path)
    try:
       assert OperatorCases(newstore).get(c["id"])["state"]=="ACKNOWLEDGED"
    finally:newstore.db.close()

def test_untrusted_local_post_without_session_rejected(harness):
    app,client,reads,path=harness
    refresh(client)
    result=decision(client,cases(client)[0])
    assert result.status_code==403

def test_cross_site_origin_rejected_even_with_token(harness):
    app,client,reads,path=harness
    refresh(client)
    headers={**session(client),"Origin":"https://untrusted.example"}
    assert decision(client,cases(client)[0],headers=headers).status_code==403

def test_decision_optimistic_concurrency_and_explicit_version(harness):
    app,client,reads,path=harness
    refresh(client)
    c=cases(client)[0]
    h=session(client)
    assert decision(client,c,headers=h).status_code==200
    assert decision(client,c,headers=h).status_code==409
    assert cases(client)[0]["version"]==2

def test_operator_decisions_idempotent_without_duplicate_ledger(harness):
    app,client,reads,path=harness
    refresh(client)
    c=cases(client)[0];h=session(client)
    idem=str(uuid.uuid4())
    first=decision(client,c,headers=h,idem=idem)
    repeat=decision(client,c,headers=h,idem=idem)
    assert first.status_code==200 and repeat.status_code==200
    assert repeat.json()["idempotent_replay"] is True
    assert len(app.case_manager().events(c["id"]))==2

def test_reusing_idempotency_key_for_different_action_fails(harness):
    app,client,reads,path=harness
    refresh(client)
    c=cases(client)[0];h=session(client);nonce=str(uuid.uuid4())
    assert decision(client,c,headers=h,idem=nonce).status_code==200
    assert decision(client,c,action="ESCALATE",headers=h,idem=nonce).status_code==409

def test_unknown_order_can_never_be_closed_as_recovered(harness):
    app,client,reads,path=harness
    reads.clear()
    reads.extend([signed_raw(opens=[OPEN],history=[OPEN]),
                  signed_raw(history=[])])
    refresh(client);refresh(client)
    c=cases(client)[0]
    assert c["kind"]=="UNRESOLVED_ORDER_OUTCOME"
    assert c["state"]=="OPEN"
    h=session(client)
    assert decision(client,c,action="CLOSE_REVIEW",headers=h).status_code==422
    assert decision(client,c,action="HOLD",headers=h).status_code==200
    assert cases(client)[0]["state"]=="HELD"

def test_failed_submission_review_can_close_without_claiming_recovery(harness):
    app,client,reads,path=harness
    refresh(client);c=cases(client)[0]
    result=decision(client,c,action="CLOSE_REVIEW",headers=session(client))
    assert result.status_code==200
    assert result.json()["state"]=="REVIEW_CLOSED"
    assert result.json()["incident_recovery_proven"] is False
    assert result.json()["last_venue_verdict"]=="NOT_RECONCILED"

def test_operational_recheck_is_signed_read_and_no_external_write(harness):
    app,client,reads,path=harness
    refresh(client)
    c=cases(client)[0]
    reads.append(signed_raw(history=[FAILED]))
    headers=session(client)
    result=client.post("/api/ops/cases/"+c["id"]+"/recheck",headers=headers)
    assert result.status_code==200,result.text
    body=result.json()
    assert body["signed_observation"]["classification"]=="AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW"
    assert body["signed_observation"]["operator_case_ingest"]["updated"]==1
    assert body["exchange_writes_enabled"] is False
    assert body["recovery_proven"] is False

def test_case_creation_rollback_on_source_inconsistency(harness,monkeypatch):
    app,client,reads,path=harness
    original=app.case_manager().ingest_verified
    def fail(*args,**kwargs):raise ValueError("source not verifiable")
    monkeypatch.setattr(app.case_manager(),"ingest_verified",fail)
    result=client.post("/api/account/live-refresh")
    assert result.status_code==503
    assert app.store.latest_account_observation()["classification"]=="NO_AUTHENTICATED_ACCOUNT_OBSERVATION"
    assert cases(client)==[]

def test_local_hash_chain_detects_mutation(harness):
    app,client,reads,path=harness
    refresh(client);c=cases(client)[0]
    assert app.case_manager().verify(c["id"])
    app.store.db.execute("UPDATE operator_case_events SET payload_json=? WHERE case_id=?",('{"fake":"proof"}',c["id"]))
    assert not app.case_manager().verify(c["id"])

def test_local_operator_cannot_issue_trade_or_fake_recovery(harness):
    app,client,reads,path=harness
    refresh(client);c=cases(client)[0];h=session(client)
    for illegal in ("CANCEL_EXCHANGE_ORDER","TRADE","MARK_RECOVERED","AUTO_RETRY"):
       assert decision(client,c,action=illegal,headers=h).status_code==422
    assert cases(client)[0]["state"]=="OPEN"
