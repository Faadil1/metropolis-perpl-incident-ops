import pytest
from order_observer import summarize_observed_orders,OrderObservationInvalid

def evidence():
    return {
       'wallet':{'mt':19,'as':[{'id':1060,'b':'DONOTLEAK'}]},
       'orders':{'mt':23,'sn':10,'d':[]},
       'positions':{'mt':26,'sn':11,'d':[]},
       'order_history':{'d':[],'np':''},
       'fills':{'d':[],'np':''},
    }
def order(st=2,acc=1060):
    return {'rq':54,'acc':acc,'mkt':16,'oid':88,'st':st,'p':12345678,'os':50000}

def test_empty_wallet_has_no_fake_trades():
    result=summarize_observed_orders(evidence())
    assert result['open_orders']['rows']==[]
    assert result['history_page_1']['rows']==[]
    assert result['outcome_certainty']=='NO_INCIDENT_INFERRED'

def test_real_open_order_sanitized_with_exchange_block():
    raw=evidence();raw['orders']['d']=[order()]
    x=summarize_observed_orders(raw)
    row=x['open_orders']['rows'][0]
    assert row['account_id']==1060 and row['request_id']==54
    assert row['source']=='AUTHENTICATED_OPEN_ORDER_SNAPSHOT'
    assert row['snapshot_block']==10
    assert row['status']=='OPEN'
    assert not row['consequence_verified']
    assert not row['incident_detected']
    import json
    assert '12345678' not in json.dumps(x)
    assert 'DONOTLEAK' not in json.dumps(x)

def test_history_fill_only_positive_evidence_not_position_consequence():
    raw=evidence();raw['order_history']['d']=[order(st=4)]
    raw['fills']['d']=[{'acc':1060,'mkt':16,'oid':88,'p':321,'s':12}]
    result=summarize_observed_orders(raw)
    row=result['history_page_1']['rows'][0]
    assert row['status']=='FILLED'
    assert row['fill_found_first_page'] is True
    assert row['consequence_verified'] is False
    assert result['outcome_certainty']=='NO_INCIDENT_INFERRED'

def test_history_cursor_explicitly_incomplete():
    raw=evidence();raw['order_history']['np']='more'
    assert summarize_observed_orders(raw)['history_has_more_pages'] is True

def test_wrong_account_refused_not_assigned_to_user():
    raw=evidence();raw['orders']['d']=[order(acc=22)]
    with pytest.raises(OrderObservationInvalid):
        summarize_observed_orders(raw)

def test_unknown_schema_refused_no_false_status():
    raw=evidence();raw['orders']['d']=[order(st=100)]
    with pytest.raises(OrderObservationInvalid):
        summarize_observed_orders(raw)

def test_limit_prevents_unbounded_ui_payload():
    raw=evidence();raw['orders']['d']=[{**order(),'rq':i+1,'oid':i+1} for i in range(12)]
    out=summarize_observed_orders(raw,limit=4)
    assert out['open_orders']['available_count']==12
    assert out['open_orders']['shown_count']==4
    assert out['open_orders']['display_truncated'] is True

def test_boolean_id_is_not_valid_integer():
    raw=evidence();raw['orders']['d']=[{**order(),'rq':True}]
    with pytest.raises(OrderObservationInvalid):
        summarize_observed_orders(raw)
