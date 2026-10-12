from observation_delta import compare_live_observations
import pytest

def snapshot(orders=0,positions=0,block=100):
    return {'classification':'AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW',
            'open_orders_count':orders,'open_positions_count':positions,
            'accounts':[{'account_id':101,'instance_id':1,'frozen':False,'order_forwarding_enabled':False}],
            'snapshot_blocks':{'wallet':block,'orders':block,'positions':block}}

def test_first_observation_is_only_baseline():
    d=compare_live_observations({'classification':'NO_AUTHENTICATED_ACCOUNT_OBSERVATION'},snapshot())
    assert d['classification']=='BASELINE_ONLY'
    assert not d['incident_detected']
    assert not d['requires_investigation']

def test_count_change_is_signal_not_failed_order():
    d=compare_live_observations(snapshot(),snapshot(orders=1))
    assert d['classification']=='ACTIVITY_CHANGE_REVIEW_ONLY'
    assert d['requires_investigation']
    assert not d['incident_detected']
    assert d['signals'][0]['interpretation']=='ACTIVITY_OBSERVED_OUTCOME_UNKNOWN'

def test_snapshot_block_regression_is_not_silent():
    d=compare_live_observations(snapshot(block=102),snapshot(block=101))
    assert len(d['signals'])==3
    assert all(s['type']=='SNAPSHOT_BLOCK_REGRESSION' for s in d['signals'])
    assert d['incident_detected'] is False

def test_different_account_set_cannot_be_compared_as_same_trader():
    new=snapshot()
    new['accounts'][0]['account_id']=999
    d=compare_live_observations(snapshot(),new)
    assert d['classification']=='ACCOUNT_SET_CHANGED_REBASE_REQUIRED'
    assert not d['incident_detected']

def test_stable_state_does_not_infer_no_order_failures():
    d=compare_live_observations(snapshot(),snapshot(block=101))
    assert d['classification']=='NO_CHANGE_OBSERVED'
    assert d['incident_detected'] is False

def test_unverified_new_observation_rejected():
    with pytest.raises(ValueError):
        compare_live_observations(snapshot(),{})
