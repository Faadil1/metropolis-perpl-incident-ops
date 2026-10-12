"""Local research API: testnet read-only, never execute a trade."""
from __future__ import annotations
import os, sqlite3, secrets, threading
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from incident_core import IncidentStore, MANUAL
from perpl_client import PerplReadClient, CredentialsUnavailable
from perpl_market import PublicMarketReader, PublicMarketUnavailable
from account_overview import from_signed_snapshots, AccountOverviewInvalid
from observation_delta import compare_live_observations
from order_observer import summarize_observed_orders
from order_lifecycle import compare_order_lifecycle
from negative_review import review_signed_negative_paths
from operations_core import OperatorCases, CaseNotFound, CaseConflict, CaseForbidden
from monitor_core import Monitor

app=FastAPI(title='Perpl Incident Operations',version='0.1.0',docs_url='/api/docs',redoc_url=None)
store=IncidentStore(os.environ.get('INCIDENT_DB_PATH',str(Path(__file__).resolve().parent/'runtime'/'incidents.sqlite3')))
operations=OperatorCases(store)
OPERATOR_SESSION=secrets.token_urlsafe(32)
LOCAL_ORIGINS={'http://127.0.0.1:8765','http://localhost:8765'}
READ_LOCK=threading.RLock()
def case_manager():
    global operations
    if operations.store is not store:
        operations=OperatorCases(store)
    return operations

@app.middleware("http")
async def local_origin_boundary(request:Request,call_next):
    # Browser-origin requests must never be allowed to trigger local signed
    # account reads/SQLite changes from an untrusted website.
    host=request.headers.get("host","").lower()
    if host not in ("127.0.0.1:8765","localhost:8765","testserver"):
        return JSONResponse({"detail":"localhost-only operator runtime"},status_code=403)
    origin=request.headers.get("origin")
    if origin and origin not in LOCAL_ORIGINS and origin!="http://testserver":
        return JSONResponse({"detail":"cross-site origin blocked"},status_code=403)
    return await call_next(request)

class CreateIncident(BaseModel):
    account_id:int=Field(gt=0)
    rq:int=Field(gt=0)
    market_id:int=Field(ge=0)
    network:str='testnet'

class ManualFrame(BaseModel):
    frame:dict

class RequestReview(BaseModel):
    owner_note:str=Field(min_length=8,max_length=1000)
class MonitorSettings(BaseModel):
    interval_seconds:int=Field(ge=15,le=3600)

class CaseDecision(BaseModel):
    action:str
    actor:str=Field(min_length=3,max_length=80)
    reason:str=Field(min_length=12,max_length=1000)
    expected_version:int=Field(ge=1)
    idempotency_key:str=Field(min_length=12,max_length=128)

def require_local_session(request:Request, session_token:str|None):
    host=request.headers.get("host","").lower()
    if host not in ("127.0.0.1:8765","localhost:8765","testserver"):
        raise HTTPException(403,"localhost only")
    origin=request.headers.get("origin")
    if origin and origin not in LOCAL_ORIGINS and origin!="http://testserver":
        raise HTTPException(403,"cross-origin decision forbidden")
    if not secrets.compare_digest(session_token or "", OPERATOR_SESSION):
        raise HTTPException(403,"local operator session required")


def incident_or_404(ident):
    try: return store.get(ident)
    except KeyError: raise HTTPException(404,'incident not found')

@app.get('/api/health')
def health():
    return {'service':'perpl-incident-operations','mode':'PRELOCK_LOCAL_ONLY','live_network_proven':False,
            'exchange_writes_enabled':False,'local_case_writes_enabled':True,'multi_user_auth_proven':False,'optional_local_monitor_running':monitor.status()['enabled'],'read_credentials_present':bool(os.environ.get('PERPL_API_KEY_READ') and os.environ.get('PERPL_API_KEY_SECRET_READ'))}

@app.get('/api/ops/session')
def owner_local_session(request:Request):
    host=request.headers.get("host","").lower()
    if host not in ("127.0.0.1:8765","localhost:8765","testserver"):
        raise HTTPException(403,"localhost only")
    origin=request.headers.get("origin")
    if origin and origin not in LOCAL_ORIGINS and origin!="http://testserver":
        raise HTTPException(403,"cross-origin session forbidden")
    return {"operator_session":OPERATOR_SESSION,"scope":"LOCAL_OWNER_ONLY",
            "exchange_writes_enabled":False,"multi_user_auth_proven":False}

@app.get('/api/ops/cases')
def list_operator_cases():
    return {"items":case_manager().list(),"source":"PERSISTED_SIGNED_TESTNET_EVIDENCE",
            "exchange_writes_enabled":False}

@app.get('/api/ops/cases/{ident}')
def fetch_operator_case(ident:str):
    try:return case_manager().get(ident)
    except CaseNotFound:raise HTTPException(404,"case not found")

@app.get('/api/ops/cases/{ident}/ledger')
def operator_case_ledger(ident:str):
    try:
        return {"events":case_manager().events(ident),
                "hash_chain_valid":case_manager().verify(ident),
                "kind":"LOCAL_TAMPER_EVIDENT_NOT_IMMUTABLE"}
    except CaseNotFound:raise HTTPException(404,"case not found")

@app.post('/api/ops/cases/{ident}/decision')
def operator_case_decision(ident:str,body:CaseDecision,request:Request,
                           x_operator_session:str|None=Header(default=None)):
    require_local_session(request,x_operator_session)
    try:
        return case_manager().decide(ident,body.action,body.actor,body.reason,
                                     body.expected_version,body.idempotency_key)
    except CaseNotFound:raise HTTPException(404,"case not found")
    except CaseConflict as exc:raise HTTPException(409,str(exc))
    except CaseForbidden as exc:raise HTTPException(422,str(exc))

@app.post('/api/ops/cases/{ident}/recheck')
def operator_case_recheck(ident:str,request:Request,
                          x_operator_session:str|None=Header(default=None)):
    require_local_session(request,x_operator_session)
    try:case=case_manager().get(ident)
    except CaseNotFound:raise HTTPException(404,"case not found")
    summary=refresh_account_overview()
    return {"requested_case_id":ident,"request_id":case["request_id"],
            "signed_observation":summary,"local_case":case_manager().get(ident),
            "recovery_proven":False,"exchange_writes_enabled":False}

@app.get('/api/incidents')
def incidents(): return {'items':store.all()}

@app.post('/api/incidents',status_code=201)
def create(req:CreateIncident):
    try:return store.create(req.network,req.account_id,req.rq,req.market_id)
    except (ValueError,sqlite3.IntegrityError) as exc:raise HTTPException(422,str(exc))

@app.get('/api/incidents/{ident}')
def get(ident:str): return incident_or_404(ident)

@app.get('/api/incidents/{ident}/ledger')
def ledger(ident:str):
    incident_or_404(ident)
    return {'events':store.ledger(ident),'hash_chain_valid':store.verify_ledger(ident)}

@app.post('/api/incidents/{ident}/manual-frame')
def manual(ident:str,req:ManualFrame):
    incident_or_404(ident)
    try:return store.apply_frame(ident,req.frame,source=MANUAL)
    except ValueError as exc:raise HTTPException(422,str(exc))

@app.post('/api/incidents/{ident}/live-refresh')
def live_refresh(ident:str):
    incident=incident_or_404(ident)
    try:
        client=PerplReadClient.from_env(incident['network'])
        client.public_context()
        return store.refresh_snapshots(ident,client.read_all())
    except (CredentialsUnavailable,ValueError) as exc:raise HTTPException(424,str(exc))
    except ConnectionError:
        store.log(ident,'LIVE_READ_FAILED',MANUAL,{'reason':'READ_UNAVAILABLE','result':'UNKNOWN'})
        raise HTTPException(503,'Read failed; outcome UNKNOWN; no exchange action performed')
    except Exception:
        raise HTTPException(503,'Perpl private read or public context unavailable; no live claim')

@app.get('/api/account/latest')
def latest_account_observation():
    return store.latest_account_observation()

@app.post('/api/account/live-refresh')
def refresh_account_overview():
    with READ_LOCK:
        return _refresh_account_impl()

def _refresh_account_impl():
    try:
        client=PerplReadClient.from_env('testnet')
        raw=client.read_all()
        summary=from_signed_snapshots(raw)
        summary['observed_orders']=summarize_observed_orders(raw)
        previous=store.latest_account_observation()
        summary['activity']=compare_live_observations(previous,summary)
        # Retain signed previously-open identities even if an intermediate refresh
        # already saw 0 active orders. READ-only and bounded to 512 local records.
        recent=store.recent_account_observations(limit=512)
        summary['order_lifecycle']=compare_order_lifecycle(previous,summary,earlier=recent)
        summary['negative_path_review']=review_signed_negative_paths(summary)
        # Atomic signed observation and source-verified operator case creation.
        # CREATE TABLE via executescript may commit an active SQLite txn.
        # Resolve/rebind case schema BEFORE beginning the observation txn.
        manager=case_manager()
        store.db.execute('BEGIN IMMEDIATE')
        try:
            receipt=store.record_account_observation(summary)
            summary['operator_case_ingest']=manager.ingest_verified(
                summary,receipt['observation_digest'])
            store.db.execute('COMMIT')
        except Exception:
            store.db.execute('ROLLBACK')
            raise
        return summary
    except CredentialsUnavailable as exc:
        raise HTTPException(424,'READ credentials not available locally')
    except (ConnectionError,AccountOverviewInvalid,ValueError):
        raise HTTPException(503,'Account read not independently verified; no observation stored.')
    except Exception:
        raise HTTPException(503,'Account read unavailable. No live claim made.')

monitor=Monitor(refresh_account_overview)

@app.get('/api/ops/monitor')
def monitor_status():
    return monitor.status()

@app.post('/api/ops/monitor/start')
def monitor_start(body:MonitorSettings,request:Request,
                  x_operator_session:str|None=Header(default=None)):
    require_local_session(request,x_operator_session)
    try:
        reply=monitor.start(body.interval_seconds)
        return {**reply,**monitor.status()}
    except ValueError as exc:
        raise HTTPException(422,str(exc))

@app.post('/api/ops/monitor/stop')
def monitor_stop(request:Request,x_operator_session:str|None=Header(default=None)):
    require_local_session(request,x_operator_session)
    return {**monitor.stop(),**monitor.status()}

@app.post('/api/incidents/{ident}/public-market-refresh')
def public_market_refresh(ident:str):
    item=incident_or_404(ident)
    if item['network']!='testnet':
        raise HTTPException(422,'testnet only')
    try:
        result=PublicMarketReader().refresh(item['market_id'])
    except PublicMarketUnavailable:
        store.log(ident,'PUBLIC_MARKET_READ_UNAVAILABLE','PERPL_PUBLIC_HTTP',
                  {'classification':'UNKNOWN','no_order_inference':True})
        raise HTTPException(503,'Public market data unavailable. Order status remains UNKNOWN.')
    store.log(ident,'LIVE_PUBLIC_MARKET_CONTEXT','PERPL_PUBLIC_HTTP',
              {**result, 'incident_id':ident})
    return result

@app.post('/api/incidents/{ident}/request-cancel-review')
def request_review(ident:str,req:RequestReview):
    incident_or_404(ident)
    try:return store.request_cancel_review(ident,req.owner_note)
    except ValueError as exc:raise HTTPException(422,str(exc))

@app.get('/',response_class=HTMLResponse)
def ui():
    return HTMLResponse((Path(__file__).resolve().parent/'operator.html').read_text(encoding='utf-8'))
