from order_lifecycle import compare_order_lifecycle

def obs(open_status="OPEN",historical=None,with_open=True,cancel_rq=None):
    key={"account_id":1060,"market_id":16,"request_id":1791657855423,
         "order_id":4580968300544}
    order={**key,"status":open_status,"status_code":2}
    h=[{**key,"request_id":cancel_rq if cancel_rq is not None else key["request_id"],
        "status":"CANCELED","status_code":historical}] if historical is not None else []
    return {"classification":"AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW",
            "accounts":[{"account_id":1060,"instance_id":1}],
            "observed_orders":{
                "open_orders":{"rows":[order] if with_open else [],"display_truncated":False},
                "history_page_1":{"rows":h,"display_truncated":False}},
            "retrieved_at":"2026-10-10T12:00:00Z"}

def test_cancel_new_request_id_same_order_id_is_verified():
    x=compare_order_lifecycle(obs(),obs(with_open=False,historical=5,cancel_rq=1791658459457))
    t=x["transitions"][0]
    assert x["classification"]=="ORDER_LIFECYCLE_REVIEW_REQUIRED"
    assert t["finding"]=="CANCELED_STATUS_OBSERVED"
    assert t["positive_matching_history"] is True
    assert t["request_id_changed_on_terminal_action"] is True
    assert t["request_id"]==1791657855423
    assert t["terminal_event_request_id"]==1791658459457
    assert not t["position_consequence_verified"]
    assert not t["incident_recovery_proven"]

def test_same_request_id_terminal_remains_valid():
    result=compare_order_lifecycle(obs(),obs(with_open=False,historical=5))
    assert result["transitions"][0]["finding"]=="CANCELED_STATUS_OBSERVED"
    assert result["transitions"][0]["request_id_changed_on_terminal_action"] is False

def test_stale_latest_observation_recovers_earlier_signed_open_evidence():
    original=obs()
    stale=obs(with_open=False,historical=5,cancel_rq=1791658459457)
    latest=obs(with_open=False,historical=5,cancel_rq=1791658459457)
    result=compare_order_lifecycle(stale,latest,earlier=[stale,original])
    assert len(result["transitions"])==1
    assert result["transitions"][0]["finding"]=="CANCELED_STATUS_OBSERVED"

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

def test_cancel_other_order_id_is_not_misjoined_even_if_rq_equal():
    a=obs();b=obs(with_open=False,historical=5)
    b["observed_orders"]["history_page_1"]["rows"][0]["order_id"]=999
    result=compare_order_lifecycle(a,b)
    assert result["transitions"][0]["finding"]=="DISAPPEARED_OUTCOME_UNKNOWN"

def test_canceled_event_other_market_is_not_misjoined():
    a=obs();b=obs(with_open=False,historical=5)
    b["observed_orders"]["history_page_1"]["rows"][0]["market_id"]=1
    result=compare_order_lifecycle(a,b)
    assert result["transitions"][0]["finding"]=="DISAPPEARED_OUTCOME_UNKNOWN"

def test_other_account_prevents_cross_account_comparison():
    a=obs(); b=obs(with_open=False,historical=5)
    b["accounts"][0]["account_id"]=999
    assert compare_order_lifecycle(a,b)["classification"]=="BASELINE_ORDER_HISTORY_UNAVAILABLE"

def test_truncated_open_snapshot_cannot_infer_disappearance():
    a=obs();b=obs(with_open=False,historical=5)
    b["observed_orders"]["open_orders"]["display_truncated"]=True
    assert compare_order_lifecycle(a,b)["classification"]=="ORDER_ROWS_TRUNCATED_CANNOT_COMPARE"

def test_conflicting_terminal_events_do_not_pick_one():
    a=obs();b=obs(with_open=False,historical=5)
    fill={**b["observed_orders"]["history_page_1"]["rows"][0],"status_code":4,"status":"FILLED"}
    b["observed_orders"]["history_page_1"]["rows"].append(fill)
    result=compare_order_lifecycle(a,b)
    assert result["transitions"][0]["finding"]=="CONFLICTING_TERMINAL_HISTORY_REVIEW"
    assert not result["transitions"][0]["positive_matching_history"]

def test_first_observation_cannot_infer_history():
    assert compare_order_lifecycle({},obs())["transitions"]==[]
