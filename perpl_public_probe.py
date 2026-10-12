"""Read-only, unauthenticated public Perpl probe for an external GitHub Actions runner.

A public Perpl API response never proves a live USER/OPERATOR core loop.
No wallet, key, signature, trading endpoint or POST is used.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import ssl
import time
import urllib.error
import urllib.request

NETWORKS = {
    "testnet": ("https://testnet.perpl.xyz/api", 10143),
    "mainnet": ("https://app.perpl.xyz/api", 143),
}
ALLOWED_ROUTES = ("/v1/pub/context", "/v1/market-data/")

def safe_get(base: str, route: str, timeout: float):
    if not (route == ALLOWED_ROUTES[0] or
            (route.startswith(ALLOWED_ROUTES[1]) and
             route.endswith(("/ticker", "/book")))):
        raise ValueError("non-public or non-allowlisted route")
    req = urllib.request.Request(
        base + route, method="GET",
        headers={"Accept": "application/json",
                 "User-Agent": "metropolis-perpl-public-preflight/0.2"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as res:
        if res.status != 200:
            raise ValueError("unexpected HTTP status")
        raw = res.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("unexpected oversized payload")
        return json.loads(raw)

def run(network: str, timeout: float=10):
    base, chain_id = NETWORKS[network]
    receipt = {
        "network": network, "expected_chain_id": chain_id,
        "checked_at_ms": int(time.time() * 1000),
        "data_classification": "PUBLIC_PROVIDER_READ_ONLY",
        "does_not_prove": ["USER_ACCOUNT_INTEGRATION", "ORDER_EXECUTION",
                           "INCIDENT_RECOVERY", "LIVE_CORE_LOOP"],
        "results": {},
        "overall": "UNVERIFIED",
    }
    try:
        c = safe_get(base, "/v1/pub/context", timeout)
        actual = c.get("chain", {}).get("chain_id") if isinstance(c, dict) else None
        markets = c.get("markets") if isinstance(c, dict) else None
        if actual != chain_id or not isinstance(markets, list) or not markets:
            raise ValueError("chain or markets mismatch")
        receipt["results"]["context"] = {
            "status": "OBSERVED", "chain_id": actual, "markets": len(markets)}
    except Exception as exc:
        receipt["results"]["context"] = {"status": "UNAVAILABLE_OR_INVALID",
                                          "error_kind": type(exc).__name__}
        receipt["overall"] = "PUBLIC_API_UNVERIFIED"
        return receipt

    # Do not assume mainnet and testnet share market IDs.
    btc = next((m for m in markets if isinstance(m, dict)
                and m.get("symbol", "").upper().startswith("BTC")
                and type(m.get("id")) is int), None)
    market = btc or next((m for m in markets if isinstance(m, dict)
                          and type(m.get("id")) is int), None)
    if market is None:
        receipt["overall"] = "CONTEXT_ONLY_OBSERVED"
        return receipt

    market_id = market["id"]
    receipt["market_id"] = market_id
    for label in ("ticker", "book"):
        try:
            payload = safe_get(base, f"/v1/market-data/{market_id}/{label}", timeout)
            if not isinstance(payload, dict):
                raise ValueError("unexpected API response schema")
            receipt["results"][label] = {"status": "OBSERVED",
                                         "response_type": "JSON_OBJECT"}
        except Exception as exc:
            receipt["results"][label] = {"status": "UNAVAILABLE_OR_INVALID",
                                         "error_kind": type(exc).__name__}
    receipt["overall"] = (
        "PUBLIC_MARKET_API_OBSERVED"
        if all(r.get("status")=="OBSERVED" for r in receipt["results"].values())
        else "PARTIAL_PUBLIC_API_OBSERVED")
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", choices=NETWORKS, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    outcome = run(args.network)
    path = pathlib.Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(outcome, sort_keys=True, indent=2)+"\n")
    print(json.dumps(outcome, sort_keys=True))
    # Network failure does not fail the unrelated local test suite.
