"""Perpl Testnet authenticated READ proof, without exposing account data.

All calls are GETs to allowlisted endpoints. No POST, wallet signature, trading or
mainnet funds. Never serialize keys, response bodies, orders or positions.
"""
from __future__ import annotations

import json
import httpx

from perpl_client import PerplReadClient, NETWORKS, READ_TARGETS

SCHEMAS={"wallet":19,"orders":23,"positions":26}
SOURCE="PERPL_TESTNET_AUTHENTICATED_READ"
DIAGNOSTIC = {
    401: "AUTH_REJECTED_CHECK_KEY_AND_SIGNATURE",
    403: "FORBIDDEN_CHECK_KEY_SCOPE",
    404: "NO_EXCHANGE_ACCOUNT_OR_ENDPOINT_NOT_FOUND",
    429: "RATE_LIMITED_RETRY_LATER",
}

def check_authenticated_read(client: PerplReadClient, transport=None, timeout=9.0):
    """Report only safe, non-sensitive status and counts (no user identifiers)."""
    if client.network!="testnet":
        raise ValueError("testnet only")
    out={"network":"testnet","chain_id":10143,
         "classification":"NO_AUTHENTICATED_EVIDENCE",
         "authenticated_core_loop_proven":False,
         "exchange_writes_enabled":False,
         "results":{}}
    base=NETWORKS["testnet"]["api"]
    with httpx.Client(timeout=timeout,follow_redirects=False,transport=transport) as http:
        for label,target in READ_TARGETS.items():
            try:
                res=http.get(base+target,headers=client.signed_get_headers(target))
                if res.status_code!=200:
                    out["results"][label]={"status":DIAGNOSTIC.get(res.status_code,"HTTP_ERROR"),
                                           "http_status":res.status_code}
                    continue
                payload=res.json()
                if not isinstance(payload,dict) or (
                   label in SCHEMAS and payload.get("mt")!=SCHEMAS[label]) or (
                   label not in SCHEMAS and not isinstance(payload.get("d"),list)):
                    out["results"][label]={"status":"SCHEMA_UNEXPECTED"}
                    continue
                entry={"status":"AUTHENTICATED_READ_OBSERVED","http_status":200}
                if label in ("orders","positions","order_history","fills"):
                    # Only expose counts, never any order, wallet or position content.
                    entry["items_in_first_page"]=len(payload.get("d",[]))
                if label in ("order_history","fills"):
                    entry["more_pages"]=bool(payload.get("np"))
                out["results"][label]=entry
            except (httpx.HTTPError,ValueError,TypeError):
                out["results"][label]={"status":"READ_UNAVAILABLE_OR_INVALID"}

    observed=sum(v["status"]=="AUTHENTICATED_READ_OBSERVED"
                 for v in out["results"].values())
    if observed==len(READ_TARGETS):
        out["classification"]=SOURCE
    elif observed:
        out["classification"]="PARTIAL_PERPL_AUTHENTICATED_READ"
    else:
        out["classification"]="AUTHENTICATED_READ_UNVERIFIED"
    return out

def main():
    from perpl_client import CredentialsUnavailable
    try:
        client=PerplReadClient.from_env("testnet")
        result=check_authenticated_read(client)
    except CredentialsUnavailable:
        result={"classification":"CREDENTIALS_MISSING_OR_INVALID_FORMAT",
                "network":"testnet","exchange_writes_enabled":False}
    except Exception:
        result={"classification":"AUTHENTICATED_READ_UNVERIFIED",
                "network":"testnet","exchange_writes_enabled":False}
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    # Avoid creating any live claim unless all authenticated endpoint schemas agree.
    return 0 if result["classification"]==SOURCE else 2

if __name__=="__main__":
    raise SystemExit(main())
