"""Public probe semantics are deliberately conservative."""
from perpl_public_probe import NETWORKS, run, safe_get

def test_networks_are_distinct():
    assert NETWORKS["testnet"][1] == 10143
    assert NETWORKS["mainnet"][1] == 143

def test_non_public_routes_forbidden():
    for bad in ("/v1/trading/wallet", "/v1/trading/orders",
                "/v1/trading/positions", "/v1/admin", "/v1/pub/context?sig=1"):
        try:
            safe_get("https://testnet.perpl.xyz/api",bad,1)
        except ValueError:
            pass
        else:
            raise AssertionError(f"forbidden path allowed: {bad}")

def test_read_failure_cannot_claim_live(monkeypatch):
    import perpl_public_probe
    def broken(base,route,timeout):
        raise ConnectionError("network not configured")
    monkeypatch.setattr(perpl_public_probe,"safe_get",broken)
    record=run("testnet")
    assert record["overall"]=="PUBLIC_API_UNVERIFIED"
    assert "LIVE_CORE_LOOP" in record["does_not_prove"]

def test_market_selection_dynamic(monkeypatch):
    import perpl_public_probe
    called=[]
    def f(base,route,timeout):
        called.append(route)
        if route=="/v1/pub/context":
            return {"chain":{"chain_id":10143},"markets":[
                {"id":16,"symbol":"BTC"},{"id":32,"symbol":"ETH"}]}
        return {"ok":True}
    monkeypatch.setattr(perpl_public_probe,"safe_get",f)
    record=run("testnet")
    assert record["overall"]=="PUBLIC_MARKET_API_OBSERVED"
    assert called[1:]==["/v1/market-data/16/ticker","/v1/market-data/16/book"]
