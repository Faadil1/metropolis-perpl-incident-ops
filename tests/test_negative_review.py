import pytest
from order_observer import summarize_observed_orders,OrderObservationInvalid
from account_overview import from_signed_snapshots
from negative_review import review_signed_negative_paths

def raw_history(rows):
    return {"wallet":{"mt":19,"sn":100,"as":[{"id":1060,"in":1,"fw":False,"fr":False,"lfr":0}]},
            "orders":{"mt":23,"sn":100,"d":[]},
            "positions":{"mt":26,"sn":100,"d":[]},
            "order_history":{"d":rows,"np":""},
            "fills":{"d":[],"np":""}}

def assessed(raw):
    overview=from_signed_snapshots(raw)
    overview["observed_orders"]=summarize_observed_orders(raw)
    overview["order_lifecycle"]={"transitions":[]}
    return review_signed_negative_paths(overview)

def test_no_incident_on_clean_real_order_lifecycle():
    order={"acc":1060,"mkt":16,"rq":10,"oid":100,"st":5}
    result=assessed(raw_history([order]))
    assert result["cases"]==[]
    assert result["review_required"] is False
    assert result["actual_live_failure_observed"] is False

def test_signed_rejection_without_onchain_oid_is_not_dropped():
    rejected={"acc":1060,"mkt":16,"rq":13,"st":7,"sr":34}
    result=assessed(raw_history([rejected]))
    case=result["cases"][0]
    assert result["actual_live_failure_observed"] is True
    assert case["order_id"] is None
    assert case["status_reason"]=="OrderForwardingNotAllowed"
    assert case["order_forwarding_enabled"] is False
    assert "Do NOT enable" in case["next_step"]
    assert case["incident_recovery_proven"] is False

def test_concurrent_clients_low_request_id_not_auto_retried():
    result=assessed(raw_history([{"acc":1060,"mkt":16,"rq":11,"oid":0,"st":7,"sr":32}]))
    assert "other active clients" in result["cases"][0]["next_step"]
    assert not result["cases"][0]["retries_authorized"]

def test_post_failure_detail_is_preserved_without_raw_amount():
    r=raw_history([{"acc":1060,"mkt":16,"rq":9,"st":7,"sr":36,"fr":7,"p":123456789}])
    x=assessed(r)["cases"][0]
    assert x["failure_reason"]=="ReferencePriceStale"
    assert "123456789" not in str(x)

def test_unrelated_account_failure_is_rejected():
    with pytest.raises(OrderObservationInvalid):
        assessed(raw_history([{"acc":99,"mkt":16,"rq":3,"st":7,"sr":34}]))

def test_open_snapshot_missing_oid_fails_closed():
    r=raw_history([])
    r["orders"]["d"]=[{"acc":1060,"mkt":16,"rq":1,"st":2}]
    with pytest.raises(OrderObservationInvalid):
        assessed(r)

def test_unknown_order_disappearance_requires_hold_and_no_retry():
    result=assessed(raw_history([]))
    # Synthetic previous/current states tested here, not a claim of live failure.
    result2=result.copy()
    raw=raw_history([])
    overview=from_signed_snapshots(raw)
    overview["observed_orders"]=summarize_observed_orders(raw)
    overview["order_lifecycle"]={"transitions":[
        {"finding":"DISAPPEARED_OUTCOME_UNKNOWN","account_id":1060,
         "market_id":16,"request_id":7,"order_id":8}]}
    x=review_signed_negative_paths(overview)
    assert x["cases"][0]["kind"]=="UNRESOLVED_ORDER_OUTCOME"
    assert x["cases"][0]["interpretation"]=="UNKNOWN_NOT_FAILED"
    assert x["cases"][0]["retries_authorized"] is False
    assert x["actual_live_failure_observed"] is False

def test_pagination_caveat_must_be_explicit():
    raw=raw_history([])
    raw["order_history"]["np"]="cursor"
    result=assessed(raw)
    assert result["first_history_page_incomplete"] is True
    assert result["review_required"] is False

def test_signed_scope_is_required():
    with pytest.raises(ValueError):
        review_signed_negative_paths({"classification":"UNSIGNED"})
