"""Protect truth boundaries: an unknown order is never silently considered failed."""
import hashlib
import sqlite3
import pytest
from incident_core import IncidentStore, MANUAL, LIVE, WS_LIVE
from perpl_client import PerplReadClient, CredentialsUnavailable
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

@pytest.fixture
def db(tmp_path):
    return IncidentStore(str(tmp_path/'incidents.sqlite3'))

@pytest.fixture
def inc(db):
    return db.create('testnet',751,1001,1)['id']

def frame(status, rq=1001, account=751, market=1, oid=92):
    return {'mt':24,'d':[{'st':status,'rq':rq,'acc':account,'mkt':market,'oid':oid}]}

def test_incident_starts_uncertain(db,inc):
    got=db.get(inc)
    assert got['status']=='SUBMISSION_UNCERTAIN'
    assert got['plan']['can_cancel'] is False

def test_manual_fill_is_not_exchange_proof(db,inc):
    result=db.apply_frame(inc,frame(4),MANUAL)
    assert result['status']=='ORDER_FILLED_CONSEQUENCE_UNVERIFIED'
    assert result['last_source']==MANUAL
    assert result['plan']['action']=='CONFIRM_FILLS_AND_POSITION'

def test_manual_order_never_allows_cancel(db,inc):
    result=db.apply_frame(inc,frame(2),MANUAL)
    assert result['status']=='KNOWN_OPEN'
    assert result['plan']['can_cancel'] is False
    with pytest.raises(ValueError):db.request_cancel_review(inc,'Please cancel this order safely')

def test_wrong_order_is_ignored(db,inc):
    db.apply_frame(inc,frame(4,rq=199),MANUAL)
    assert db.get(inc)['status']=='SUBMISSION_UNCERTAIN'

def test_deduplicates_order_updates(db,inc):
    f=frame(2)
    db.apply_frame(inc,f,MANUAL)
    n=len(db.ledger(inc))
    db.apply_frame(inc,f,MANUAL)
    assert len(db.ledger(inc))==n

def test_late_failure_does_not_erase_fill(db,inc):
    db.apply_frame(inc,frame(4),MANUAL)
    db.apply_frame(inc,frame(7),MANUAL)
    assert db.get(inc)['status']=='ORDER_FILLED_CONSEQUENCE_UNVERIFIED'

def test_conflicting_terminal_updates_trigger_review(db,inc):
    db.apply_frame(inc,frame(4),MANUAL)
    db.apply_frame(inc,frame(5),MANUAL)
    assert db.get(inc)['status']=='CONFLICT_RECONCILE_REQUIRED'

def test_manual_frames_cannot_anchor_socket_sequence(db,inc):
    db.apply_frame(inc,{'mt':19,'sn':33},MANUAL)
    assert db.get(inc)['frame_seq'] is None

def test_ws_gap_requires_reconnect(db,inc):
    db.apply_frame(inc,{'mt':19,'sn':33,'d':{}},WS_LIVE)
    db.apply_frame(inc,{'mt':100,'sn':35},WS_LIVE)
    result=db.get(inc)
    assert result['ws_gap']==1
    assert result['plan']['action']=='RECONNECT_AND_RECONCILE'

def test_ws_reanchor_after_gap(db,inc):
    db.apply_frame(inc,{'mt':19,'sn':33,'d':{}},WS_LIVE)
    db.apply_frame(inc,{'mt':100,'sn':35},WS_LIVE)
    db.apply_frame(inc,{'mt':19,'sn':36,'d':{}},WS_LIVE)
    assert db.get(inc)['ws_gap']==0

def test_authenticated_snapshot_without_fill_preserves_unknown(db,inc):
    snaps={'wallet':{'mt':19,'d':{}},'orders':{'mt':23,'d':[]},'positions':{'mt':26,'d':[]}}
    result=db.refresh_snapshots(inc,snaps,LIVE)
    assert result['status']=='SUBMISSION_UNCERTAIN'
    assert result['last_source']==LIVE

def test_live_order_snapshot_allows_only_review_not_execution(db,inc):
    db.apply_frame(inc,frame(2),WS_LIVE)
    snaps={'wallet':{'mt':19,'d':{}},'orders':{'mt':23,'d':[{'rq':1001,'acc':751,'mkt':1,'oid':92}]},'positions':{'mt':26,'d':[]}}
    result=db.refresh_snapshots(inc,snaps,LIVE)
    assert result['plan']['can_cancel'] is True
    receipt=db.request_cancel_review(inc,'Owner wants order cancellation')
    assert receipt['state']=='REVIEW_ONLY_NOT_EXECUTED'
    assert receipt['exchange_write']=='NOT_IMPLEMENTED'

def test_local_ledger_integrity_not_immutable(db,inc):
    assert db.verify_ledger(inc)
    db.db.execute('UPDATE incident_events SET payload_json=? WHERE incident_id=?',('{"tampered":true}',inc))
    assert not db.verify_ledger(inc)

def test_cannot_create_mainnet_incident(db):
    with pytest.raises(ValueError):db.create('mainnet',751,1001,1)

def test_missing_read_key(monkeypatch):
    monkeypatch.delenv('PERPL_API_KEY_READ',raising=False)
    monkeypatch.delenv('PERPL_API_KEY_SECRET_READ',raising=False)
    with pytest.raises(CredentialsUnavailable):PerplReadClient.from_env('testnet')

def test_read_signing_cannot_sign_post():
    client=PerplReadClient('testnet','safe-test-key',Ed25519PrivateKey.generate())
    with pytest.raises(ValueError):client.signed_get_headers('/v1/trading/orders?force=true')
    with pytest.raises(ValueError):client.signed_get_headers('/v1/trading/withdraw')

def test_valid_read_signature_is_deterministic_with_fixed_nonce():
    signer=Ed25519PrivateKey.generate()
    client=PerplReadClient('testnet','key',signer)
    h1=client.signed_get_headers('/v1/trading/orders',timestamp_ms=1000000,nonce='nonce')
    h2=client.signed_get_headers('/v1/trading/orders',timestamp_ms=1000000,nonce='nonce')
    assert h1==h2 and h1['X-API-Signature']
