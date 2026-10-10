from order_lifecycle import compare_order_lifecycle

def obs(open_status="OPEN",historical=None,with_open=True):
    key={"account_id":1060,"market_id":16,"request_id":1791657855423,
         "order_id":4580968300544}
    order={**key,"status":open_status,"status_code":2}
    h=[{**key,"status":"CANCELED","status_code":historical}] if historical is not None else []
    return {
        "classification":"AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW",
        "accounts":[{"account_id":1060,"instance_id":1}],
        "observed_orders":{
            "open_orders":{"rows":[order] if with_open else [],"display_truncated":False},
            "history_page_1":{"rows":h,"display_truncated":False}
        }
    }

def test_matched_cancel_positive_exchange_status_not_incident_recovery():
    a=obs()
    b=obs(with_open=False,historical=5)
    found=compare_order_lifecycle(a,b)
    assert found["classification"]=="ORDER_LIFECYCLE_REVIEW_REQUIRED"
    t=found["transitions"][0]
    assert t["finding"]=="CANCELED_STATUS_OBSERVED"
    assert t["positive_matching_history"]
    assert not t["position_consequence_verified"]
    assert not t["incident_recovery_proven"]
    assert t["request_id"]==1791657855423

def test_disappearance_alone_is_unknown():
    result=compare_order_lifecycle(obs(),obs(with_open=False))
    assert result["transitions"][0]["finding"]=="DISAPPEARED_OUTCOME_UNKNOWN"
    assert result["transitions"][0]["positive_matching_history"] is False

def test_filled_history_not_assumed_canceled_or_position_verified():
    result=compare_order_lifecycle(obs(),obs(with_open=False,historical=4))
    assert result["transitions"][0]["finding"]=="FILLED_STATUS_OBSERVED"
    assert result["position_consequence_verified"] is False

def test_currently_open_order_has_no_transition():
    result=compare_order_lifecycle(obs(),obs(with_open=True,historical=5))
    assert result["transitions"]==[]

def test_history_for_other_order_is_not_misjoined():
    a=obs()
    b=obs(with_open=False,historical=5)
    b["observed_orders"]["history_page_1"]["rows"][0]["order_id"]=999
    result=compare_order_lifecycle(a,b)
    assert result["transitions"][0]["finding"]=="DISAPPEARED_OUTCOME_UNKNOWN"

def test_other_account_prevents_cross_account_comparison():
    a=obs(); b=obs(with_open=False,historical=5)
    b["accounts"][0]["account_id"]=999
    assert compare_order_lifecycle(a,b)["classification"]=="ACCOUNT_REBASE_REQUIRED"

def test_truncated_open_snapshot_cannot_infer_disappearance():
    a=obs();b=obs(with_open=False,historical=5)
    b["observed_orders"]["open_orders"]["display_truncated"]=True
    assert compare_order_lifecycle(a,b)["classification"]=="ORDER_ROWS_TRUNCATED_CANNOT_COMPARE"

def test_first_observation_cannot_infer_history():
    assert compare_order_lifecycle({},obs())["transitions"]==[]
