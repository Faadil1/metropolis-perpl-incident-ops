"""Venue-history reconciliation must preserve UNKNOWN in the absence of positive evidence."""
import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from incident_core import IncidentStore, LIVE
from perpl_client import PerplReadClient


def payload(rq=1001, oid=77, status=4):
    return {
        'wallet': {'mt':19,'d':{}},
        'orders': {'mt':23,'d':[]},
        'positions': {'mt':26,'d':[]},
        'order_history': {'d':[{'rq':rq,'acc':751,'mkt':16,'oid':oid,'st':status}],'np':''},
        'fills': {'d':[{'oid':oid,'acc':751,'mkt':16,'s':10}],'np':''},
    }


def test_authenticated_history_matches_order_and_fill(tmp_path):
    store=IncidentStore(str(tmp_path/'inc.sqlite3'))
    ident=store.create('testnet',751,1001,16)['id']
    item=store.refresh_snapshots(ident,payload(),LIVE)
    assert item['status']=='FILL_CONFIRMED_POSITION_RECONCILIATION_NEEDED'
    assert item['plan']['action']=='CONFIRM_FILLS_AND_POSITION'
    assert item['plan']['can_cancel'] is False
    assert item['last_source']==LIVE
    assert 'FILL_HISTORY_CONFIRMED' in [e['kind'] for e in store.ledger(ident)]


def test_no_history_match_does_not_prove_failure(tmp_path):
    store=IncidentStore(str(tmp_path/'inc.sqlite3'))
    ident=store.create('testnet',751,1001,16)['id']
    p=payload(rq=2999)
    p['order_history']['np']='next-page-cursor'
    item=store.refresh_snapshots(ident,p,LIVE)
    assert item['status']=='SUBMISSION_UNCERTAIN'
    assert item['plan']['action']=='HOLD_AND_RECONCILE'
    assert store.verify_ledger(ident)


def test_fill_from_another_market_is_not_match(tmp_path):
    store=IncidentStore(str(tmp_path/'inc.sqlite3'))
    ident=store.create('testnet',751,1001,16)['id']
    p=payload()
    p['fills']['d'][0]['mkt']=32
    item=store.refresh_snapshots(ident,p,LIVE)
    assert item['status']=='ORDER_FILLED_CONSEQUENCE_UNVERIFIED'


def test_latest_known_cancel_from_history(tmp_path):
    store=IncidentStore(str(tmp_path/'inc.sqlite3'))
    ident=store.create('testnet',751,1001,16)['id']
    p=payload(status=5)
    p['fills']['d']=[]
    item=store.refresh_snapshots(ident,p,LIVE)
    assert item['status']=='ORDER_CANCELED'
    assert item['plan']['action']=='RECONCILE_HISTORY_AND_POSITION'


def test_read_client_history_is_signed_and_read_only():
    client=PerplReadClient('testnet','fake-local-test',Ed25519PrivateKey.generate())
    calls=[]
    def handler(request):
        calls.append((request.method,request.url.path,request.url.query))
        assert request.method=='GET'
        assert request.headers.get('X-API-Signature')
        if request.url.path.endswith('/wallet'):
            return httpx.Response(200,json={'mt':19,'d':{}})
        if request.url.path.endswith('/orders'):
            return httpx.Response(200,json={'mt':23,'d':[]})
        if request.url.path.endswith('/positions'):
            return httpx.Response(200,json={'mt':26,'d':[]})
        if request.url.path.endswith('/order-history'):
            return httpx.Response(200,json={'d':[],'np':''})
        if request.url.path.endswith('/fills'):
            return httpx.Response(200,json={'d':[],'np':''})
        raise AssertionError('unexpected URL')
    data=client.read_all(transport=httpx.MockTransport(handler))
    assert len(calls)==5
    assert 'fills' in data and 'order_history' in data
    assert sum(1 for method,*_ in calls if method=='GET')==5
