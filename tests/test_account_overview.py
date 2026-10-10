import pytest
from account_overview import from_signed_snapshots, AccountOverviewInvalid

def fixture():
    return {
        'wallet': {'mt':19,'sn':120,'addr':'0xSHOULD_NOT_LEAK','as':[
            {'id':712,'in':1,'fw':False,'fr':False,'lfr':0,'b':'100000000'},
            {'id':713,'in':2,'fw':True,'fr':True,'lfr':47,'b':'0'}]},
        'orders':{'mt':23,'sn':121,'d':[]},
        'positions':{'mt':26,'sn':122,'d':[]},
        'order_history':{'d':[],'np':'next'},
        'fills':{'d':[],'np':''},
    }

def test_authenticated_account_overview_sanitized():
    doc=from_signed_snapshots(fixture())
    assert len(doc['accounts'])==2
    assert doc['accounts'][0]['account_id']==712
    assert doc['accounts'][1]['order_forwarding_enabled'] is True
    assert doc['history']['order_history']['has_more_pages'] is True
    assert doc['non_atomic_http_reads'] is True
    assert doc['live_core_loop_proven'] is False
    import json
    blob=json.dumps(doc)
    assert "0xSHOULD_NOT_LEAK" not in blob
    assert '100000000' not in blob

def test_missing_wallet_as_rejected():
    p=fixture()
    p['wallet']={'mt':19,'d':{}}
    with pytest.raises(AccountOverviewInvalid):
        from_signed_snapshots(p)

def test_wallet_invalid_flags_are_not_inferred():
    p=fixture()
    del p['wallet']['as'][0]['fw']
    with pytest.raises(AccountOverviewInvalid):
        from_signed_snapshots(p)

def test_history_shape_required():
    p=fixture()
    p['fills']={'d':{},'np':''}
    with pytest.raises(AccountOverviewInvalid):
        from_signed_snapshots(p)

def test_zero_open_orders_is_not_terminal_outcome():
    p=fixture()
    doc=from_signed_snapshots(p)
    assert doc['open_orders_count']==0
    assert 'cannot prove' in doc['note']
