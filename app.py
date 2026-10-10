"""Local research API: testnet read-only, never execute a trade."""
from __future__ import annotations
import os, sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from incident_core import IncidentStore, MANUAL
from perpl_client import PerplReadClient, CredentialsUnavailable
from perpl_market import PublicMarketReader, PublicMarketUnavailable
from account_overview import from_signed_snapshots, AccountOverviewInvalid
from observation_delta import compare_live_observations

app=FastAPI(title='Perpl Incident Operations',version='0.1.0',docs_url='/api/docs',redoc_url=None)
store=IncidentStore(os.environ.get('INCIDENT_DB_PATH',str(Path(__file__).resolve().parent/'runtime'/'incidents.sqlite3')))

class CreateIncident(BaseModel):
    account_id:int=Field(gt=0)
    rq:int=Field(gt=0)
    market_id:int=Field(ge=0)
    network:str='testnet'

class ManualFrame(BaseModel):
    frame:dict

class RequestReview(BaseModel):
    owner_note:str=Field(min_length=8,max_length=1000)

def incident_or_404(ident):
    try: return store.get(ident)
    except KeyError: raise HTTPException(404,'incident not found')

@app.get('/api/health')
def health():
    return {'service':'perpl-incident-operations','mode':'PRELOCK_LOCAL_ONLY','live_network_proven':False,
            'exchange_writes_enabled':False,'read_credentials_present':bool(os.environ.get('PERPL_API_KEY_READ') and os.environ.get('PERPL_API_KEY_SECRET_READ'))}

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
    try:
        client=PerplReadClient.from_env('testnet')
        raw=client.read_all()
        summary=from_signed_snapshots(raw)
        previous=store.latest_account_observation()
        summary['activity']=compare_live_observations(previous,summary)
        store.record_account_observation(summary)
        return summary
    except CredentialsUnavailable as exc:
        raise HTTPException(424,'READ credentials not available locally')
    except (ConnectionError,AccountOverviewInvalid,ValueError):
        raise HTTPException(503,'Account read not independently verified; no observation stored.')
    except Exception:
        raise HTTPException(503,'Account read unavailable. No live claim made.')

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
