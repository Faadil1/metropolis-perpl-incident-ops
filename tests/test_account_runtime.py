from fastapi.testclient import TestClient
from incident_core import IncidentStore
from account_overview import from_signed_snapshots

def signed_example():
    return {
        'wallet':{'mt':19,'sn':456,'addr':'sensitive-private-address','as':[
            {'id':800,'in':11,'fw':False,'fr':False,'lfr':0,'b':'100000000'}]},
        'orders':{'mt':23,'sn':456,'d':[]},
        'positions':{'mt':26,'sn':457,'d':[]},
        'order_history':{'d':[],'np':''},
        'fills':{'d':[],'np':''}
    }

def test_summary_persists_across_restarts_without_secrets(tmp_path):
    path=str(tmp_path/'operators.sqlite3')
    first=IncidentStore(path)
    summary=from_signed_snapshots(signed_example())
    receipt=first.record_account_observation(summary)
    assert receipt['classification']=='AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW'
    second=IncidentStore(path)
    latest=second.latest_account_observation()
    assert latest['accounts'][0]['account_id']==800
    assert latest['open_orders_count']==0
    assert 'sensitive-private-address' not in str(latest)
    assert '100000000' not in str(latest)

def test_reject_unverified_summary_persistence(tmp_path):
    import pytest
    store=IncidentStore(str(tmp_path/'operators.sqlite3'))
    with pytest.raises(ValueError):
        store.record_account_observation({'classification':'MANUAL_UNVERIFIED'})
    assert store.latest_account_observation()['classification']=='NO_AUTHENTICATED_ACCOUNT_OBSERVATION'

def test_local_operator_account_endpoint_reports_truth(monkeypatch,tmp_path):
    import importlib
    monkeypatch.setenv('INCIDENT_DB_PATH',str(tmp_path/'local.sqlite3'))
    app_module=importlib.import_module('app')
    app_module.store=IncidentStore(str(tmp_path/'local.sqlite3'))
    class FakeReadClient:
        @classmethod
        def from_env(cls, network):
            assert network=='testnet'
            return cls()
        def read_all(self):
            return signed_example()
    monkeypatch.setattr(app_module,'PerplReadClient',FakeReadClient)
    client=TestClient(app_module.app)
    response=client.post('/api/account/live-refresh')
    assert response.status_code==200
    body=response.json()
    assert body['classification']=='AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW'
    assert body['open_orders_count']==0
    assert body['incident_recovery_proven'] is False
    assert 'sensitive-private-address' not in response.text
    assert client.get('/api/account/latest').json()['accounts'][0]['account_id']==800

def test_wallet_snapshot_schema_fix_in_incident_reconciliation(tmp_path):
    store=IncidentStore(str(tmp_path/'operators.sqlite3'))
    incident=store.create('testnet',800,1001,16)['id']
    result=store.refresh_snapshots(incident,signed_example())
    assert result['status']=='SUBMISSION_UNCERTAIN'
    assert result['plan']['can_cancel'] is False
    assert store.verify_ledger(incident)

def test_live_account_second_observation_records_review_only_delta(monkeypatch,tmp_path):
    import importlib
    app_module=importlib.import_module('app')
    app_module.store=IncidentStore(str(tmp_path/'observations.sqlite3'))
    responses=[signed_example(),signed_example()]
    responses[1]['orders']['d']=[{'rq':25,'oid':99,'acc':800,'mkt':16,'st':2}]
    class SequencedReadClient:
        @classmethod
        def from_env(cls, network):
            assert network=='testnet'
            return cls()
        def read_all(self):
            return responses.pop(0)
    monkeypatch.setattr(app_module,'PerplReadClient',SequencedReadClient)
    client=TestClient(app_module.app)
    baseline=client.post('/api/account/live-refresh')
    assert baseline.status_code==200
    assert baseline.json()['activity']['classification']=='BASELINE_ONLY'
    observed=client.post('/api/account/live-refresh')
    assert observed.status_code==200
    assert observed.json()['activity']['classification']=='ACTIVITY_CHANGE_REVIEW_ONLY'
    assert observed.json()['activity']['requires_investigation'] is True
    assert observed.json()['activity']['incident_detected'] is False
    assert observed.json()['open_orders_count']==1
    assert client.get('/api/incidents').json()['items']==[]
    assert client.get('/api/account/latest').json()['activity']['incident_detected'] is False

def test_operator_read_includes_only_real_signed_order_data(monkeypatch,tmp_path):
    import importlib
    app_module=importlib.import_module('app')
    app_module.store=IncidentStore(str(tmp_path/'observed.sqlite3'))
    raw=signed_example()
    raw['orders']['d']=[{'acc':800,'mkt':16,'rq':91,'oid':77,'st':2,'p':123,'s':45}]
    class GenuineRead:
        @classmethod
        def from_env(cls,network):
            assert network=='testnet'
            return cls()
        def read_all(self):
            return raw
    monkeypatch.setattr(app_module,'PerplReadClient',GenuineRead)
    cli=TestClient(app_module.app)
    result=cli.post('/api/account/live-refresh')
    assert result.status_code==200
    observed=result.json()['observed_orders']['open_orders']['rows']
    assert len(observed)==1
    assert observed[0]['request_id']==91
    assert observed[0]['source']=='AUTHENTICATED_OPEN_ORDER_SNAPSHOT'
    assert observed[0]['incident_detected'] is False
    assert '"p": 123' not in result.text
    assert cli.get('/api/incidents').json()['items']==[]

def test_signed_open_then_cancel_lifecycle_not_called_incident(monkeypatch,tmp_path):
    import importlib
    app_module=importlib.import_module('app')
    app_module.store=IncidentStore(str(tmp_path/'lifecycle.sqlite3'))
    a=signed_example()
    a['orders']['d']=[{'acc':800,'mkt':16,'rq':908,'oid':77,'st':2}]
    a['order_history']['d']=[{'acc':800,'mkt':16,'rq':908,'oid':77,'st':2}]
    b=signed_example()
    b['order_history']['d']=[{'acc':800,'mkt':16,'rq':908,'oid':77,'st':5}]
    stream=[a,b]
    class MockRead:
        @classmethod
        def from_env(cls,network):
            return cls()
        def read_all(self):
            return stream.pop(0)
    monkeypatch.setattr(app_module,'PerplReadClient',MockRead)
    client=TestClient(app_module.app)
    first=client.post('/api/account/live-refresh')
    assert first.status_code==200
    assert first.json()['order_lifecycle']['transitions']==[]
    second=client.post('/api/account/live-refresh')
    assert second.status_code==200
    assert second.json()['order_lifecycle']['transitions'][0]['finding']=='CANCELED_STATUS_OBSERVED'
    assert second.json()['order_lifecycle']['incident_recovery_proven'] is False
    assert client.get('/api/incidents').json()['items']==[]
    last=client.get('/api/account/latest')
    assert last.json()['order_lifecycle']['transitions'][0]['order_id']==77

def test_real_perpl_cancel_different_rq_recovers_from_persisted_open_after_restart(monkeypatch,tmp_path):
    """Regression from owner video, 2026-10-11 (UTC Oct 12):
    original open rq differs from cancel command rq, oid stays unchanged.
    """
    import importlib
    app_module=importlib.import_module('app')
    location=str(tmp_path/'owner-history.sqlite3')
    app_module.store=IncidentStore(location)
    original=signed_example()
    original['orders']['d']=[{
        'acc':800,'mkt':16,'oid':4580968300544,'rq':1791657855423,'st':2
    }]
    original['order_history']['d']=[{
        'acc':800,'mkt':16,'oid':4580968300544,'rq':1791657855423,'st':2
    }]
    canceled=signed_example()
    canceled['order_history']['d']=[
        {'acc':800,'mkt':16,'oid':4580968300544,'rq':1791658459457,'st':5},
        {'acc':800,'mkt':16,'oid':4580968300544,'rq':1791657855423,'st':2},
    ]
    stream=[original,canceled,canceled]
    class SimulatedHttp:
        @classmethod
        def from_env(cls,network):
            assert network=='testnet'
            return cls()
        def read_all(self):
            return stream.pop(0)
    monkeypatch.setattr(app_module,'PerplReadClient',SimulatedHttp)
    client=TestClient(app_module.app)
    first=client.post('/api/account/live-refresh')
    assert first.status_code==200
    assert first.json()['open_orders_count']==1
    second=client.post('/api/account/live-refresh')
    assert second.status_code==200
    events=second.json()['order_lifecycle']['transitions']
    assert len(events)==1
    assert events[0]['finding']=='CANCELED_STATUS_OBSERVED'
    assert events[0]['request_id']==1791657855423
    assert events[0]['terminal_event_request_id']==1791658459457
    assert events[0]['request_id_changed_on_terminal_action'] is True
    # Simulate process restart. Latest snapshot has 0 open orders, but
    # previous signed OPEN exists in the SQLite local evidence history.
    app_module.store=IncidentStore(location)
    third=client.post('/api/account/live-refresh')
    assert third.status_code==200
    events=third.json()['order_lifecycle']['transitions']
    assert len(events)==1
    assert events[0]['finding']=='CANCELED_STATUS_OBSERVED'
    assert third.json()['open_orders_count']==0
    assert third.json()['open_positions_count']==0
    assert third.json()['order_lifecycle']['incident_recovery_proven'] is False
    assert client.get('/api/incidents').json()['items']==[]

def test_no_prior_signed_open_does_not_create_false_transition(monkeypatch,tmp_path):
    import importlib
    app_module=importlib.import_module('app')
    app_module.store=IncidentStore(str(tmp_path/'no-open.sqlite3'))
    raw=signed_example()
    raw['order_history']['d']=[
       {'acc':800,'mkt':16,'oid':4580968300544,'rq':1791658459457,'st':5},
    ]
    class ReadClient:
        @classmethod
        def from_env(cls,network):
            return cls()
        def read_all(self):
            return raw
    monkeypatch.setattr(app_module,'PerplReadClient',ReadClient)
    response=TestClient(app_module.app).post('/api/account/live-refresh')
    assert response.status_code==200
    assert response.json()['order_lifecycle']['transitions']==[]
    assert response.json()['order_lifecycle']['incident_recovery_proven'] is False

def test_signed_api_failure_missing_oid_reaches_operator_review(monkeypatch,tmp_path):
    import importlib
    app_module=importlib.import_module('app')
    app_module.store=IncidentStore(str(tmp_path/'perpl-failed-order.sqlite3'))
    raw=signed_example()
    raw['order_history']['d']=[{'acc':800,'mkt':16,'rq':454,'st':7,'sr':34}]
    class MockSignedPerpl:
        @classmethod
        def from_env(cls,network):
            assert network=='testnet'
            return cls()
        def read_all(self):
            return raw
    monkeypatch.setattr(app_module,'PerplReadClient',MockSignedPerpl)
    client=TestClient(app_module.app)
    response=client.post('/api/account/live-refresh')
    assert response.status_code==200, response.text
    cases=response.json()['negative_path_review']['cases']
    assert len(cases)==1
    assert cases[0]['kind']=='POSITIVE_EXCHANGE_FAILURE_EVENT'
    assert cases[0]['status_reason']=='OrderForwardingNotAllowed'
    assert cases[0]['order_id'] is None
    assert cases[0]['incident_recovery_proven'] is False
    assert cases[0]['retries_authorized'] is False
    assert client.get('/api/incidents').json()['items']==[]

def test_no_failure_claim_when_only_forwarding_disabled(monkeypatch,tmp_path):
    import importlib
    app_module=importlib.import_module('app')
    app_module.store=IncidentStore(str(tmp_path/'perpl-normal.sqlite3'))
    raw=signed_example()
    class MockSignedPerpl:
        @classmethod
        def from_env(cls,network):
            return cls()
        def read_all(self):
            return raw
    monkeypatch.setattr(app_module,'PerplReadClient',MockSignedPerpl)
    r=TestClient(app_module.app).post('/api/account/live-refresh')
    assert r.status_code==200
    assert r.json()['negative_path_review']['review_required'] is False
    assert r.json()['negative_path_review']['actual_live_failure_observed'] is False
