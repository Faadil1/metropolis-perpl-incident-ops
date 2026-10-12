"""Signed bounded history pagination: protect exchange truth across pages."""
import pytest
import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from perpl_client import PerplReadClient
from account_overview import from_signed_snapshots
from order_observer import summarize_observed_orders
from negative_review import review_signed_negative_paths


def client():
    return PerplReadClient("testnet","safe-read-test",Ed25519PrivateKey.generate())


def exchange_handler(calls, history_cursor=""):
    def handler(req):
        assert req.method=="GET"
        assert req.headers.get("X-API-Signature")
        assert req.url.host=="testnet.perpl.xyz"
        calls.append(str(req.url))
        path=req.url.path
        if path.endswith("/wallet"):
            return httpx.Response(200,json={"mt":19,"sn":40,"as":[
                {"id":1060,"in":1,"fw":False,"fr":False,"lfr":0}]})
        if path.endswith("/orders"):
            return httpx.Response(200,json={"mt":23,"sn":41,"d":[]})
        if path.endswith("/positions"):
            return httpx.Response(200,json={"mt":26,"sn":42,"d":[]})
        if path.endswith("/order-history"):
            if "page" in req.url.params:
                assert req.url.params["page"]=="token2"
                return httpx.Response(200,json={"d":[{
                    "acc":1060,"mkt":16,"rq":44,"st":7,"sr":34
                }],"np":history_cursor})
            return httpx.Response(200,json={"d":[],"np":"token2"})
        if path.endswith("/fills"):
            return httpx.Response(200,json={"d":[],"np":""})
        return httpx.Response(404)
    return handler


def test_second_page_signed_failure_opens_source_bound_review():
    seen=[]
    raw=client().read_all(transport=httpx.MockTransport(exchange_handler(seen)))
    assert raw["order_history_scan"]["page_count"]==2
    assert raw["order_history_scan"]["complete"] is True
    assert len(seen)==6
    summary=from_signed_snapshots(raw)
    summary["observed_orders"]=summarize_observed_orders(raw)
    review=review_signed_negative_paths(summary)
    assert len(review["cases"])==1
    assert review["cases"][0]["status_reason"]=="OrderForwardingNotAllowed"
    assert review["cases"][0]["evidence"]=="PERPL_SIGNED_BOUNDED_HISTORY"
    assert summary["history"]["order_history"]["events_scanned"]==1
    assert summary["history"]["order_history"]["pages_scanned"]==2
    assert summary["history"]["order_history"]["scan_complete"] is True
    assert summary["incident_recovery_proven"] is False
    assert raw["order_history"]["d"]==[]


def test_incomplete_cap_preserves_unknown_and_records_scope():
    seen=[]
    raw=client().read_all(transport=httpx.MockTransport(exchange_handler(seen,history_cursor="token3")),
                          max_history_pages=2)
    assert raw["order_history_scan"]["complete"] is False
    summary=from_signed_snapshots(raw)
    assert summary["history"]["order_history"]["scan_complete"] is False
    assert summary["non_atomic_http_reads"] is True


def test_bad_follow_up_endpoint_is_never_signed():
    c=client()
    with pytest.raises(ValueError):
        c.signed_get_headers("/v1/trading/order-history?count=100&page=x&withdraw=true")
    with pytest.raises(ValueError):
        c.signed_get_headers("/v1/trading/order-history?page=x&count=100")
    with pytest.raises(ValueError):
        c.signed_get_headers("/v1/trading/order-history?count=100&page=")
    with pytest.raises(ValueError):
        c.history_target("orders","token2")


def test_same_cursor_loop_fails_without_storing_partial_live_result():
    seen=[]
    with pytest.raises(ConnectionError):
        client().read_all(transport=httpx.MockTransport(exchange_handler(seen,history_cursor="token2")),
                          max_history_pages=4)


def test_exchange_cursor_restricted_by_size_and_characters():
    c=client()
    for cursor in ("", "x"*257, "\nsecret", "\t", "contains space"):
        with pytest.raises(ValueError):
            c.history_target("fills",cursor)
    assert c.history_target("fills","abc/+=?").startswith("/v1/trading/fills?count=100&page=")


def test_no_exchange_write_or_production_claim_even_after_pages():
    seen=[]
    raw=client().read_all(transport=httpx.MockTransport(exchange_handler(seen)))
    summary=from_signed_snapshots(raw)
    assert summary["exchange_writes_enabled"] is False
    assert summary["live_core_loop_proven"] is False
    assert all("/v1/trading/" in path for path in seen)
