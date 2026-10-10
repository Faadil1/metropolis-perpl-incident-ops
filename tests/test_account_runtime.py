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
