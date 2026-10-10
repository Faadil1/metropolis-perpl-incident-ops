import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from perpl_client import PerplReadClient
from perpl_auth_check import check_authenticated_read


def mock_response(request):
    assert request.method=="GET"
    assert request.url.host=="testnet.perpl.xyz"
    assert request.headers.get("X-API-Signature")
    path=request.url.path
    if path.endswith("/wallet"):
        return httpx.Response(200,json={"mt":19,"d":{"wallet":"should-not-be-printed","as":[]}})
    if path.endswith("/orders"):
        return httpx.Response(200,json={"mt":23,"d":[{"secret":"order-info"}]})
    if path.endswith("/positions"):
        return httpx.Response(200,json={"mt":26,"d":[]})
    if path.endswith("/order-history"):
        return httpx.Response(200,json={"d":[],"np":"cursor"})
    if path.endswith("/fills"):
        return httpx.Response(200,json={"d":[],"np":""})
    raise AssertionError("endpoint not allowlisted")


def test_all_reads_sanitized():
    client=PerplReadClient("testnet","highly-private-api-token",Ed25519PrivateKey.generate())
    result=check_authenticated_read(client,transport=httpx.MockTransport(mock_response))
    import json
    serialized=json.dumps(result)
    assert result["classification"]=="PERPL_TESTNET_AUTHENTICATED_READ"
    assert result["authenticated_core_loop_proven"] is False
    assert result["exchange_writes_enabled"] is False
    assert result["results"]["orders"]["items_in_first_page"]==1
    assert result["results"]["order_history"]["more_pages"] is True
    assert "highly-private-api-token" not in serialized
    assert "should-not-be-printed" not in serialized
    assert "order-info" not in serialized


def test_no_account_is_not_a_live_claim():
    client=PerplReadClient("testnet","fake-token",Ed25519PrivateKey.generate())
    def handler(request):
        return httpx.Response(404,json={"error":"wallet with no account"})
    result=check_authenticated_read(client,transport=httpx.MockTransport(handler))
    assert result["classification"]=="AUTHENTICATED_READ_UNVERIFIED"
    assert result["results"]["wallet"]["http_status"]==404


def test_partial_success_never_claims_full_read():
    client=PerplReadClient("testnet","fake-token",Ed25519PrivateKey.generate())
    def handler(request):
        if request.url.path.endswith("/wallet"):
            return httpx.Response(200,json={"mt":19,"d":{}})
        return httpx.Response(403,json={"error":"forbidden"})
    result=check_authenticated_read(client,transport=httpx.MockTransport(handler))
    assert result["classification"]=="PARTIAL_PERPL_AUTHENTICATED_READ"
    assert result["results"]["positions"]["status"]=="FORBIDDEN_CHECK_KEY_SCOPE"
