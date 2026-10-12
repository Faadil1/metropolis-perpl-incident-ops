"""Sanitized observation of genuinely present Perpl orders, NEVER inferred incidents.

The caller supplies successful signed-GET payloads. Rows originate only from
Perpl open-order snapshot or first history page. No trade/wallet writes, no
synthetic request IDs, no raw wallet/price/size data in the returned object.
"""
from __future__ import annotations

STATUSES = {
    0:"UNSPECIFIED",1:"PENDING",2:"OPEN",3:"PARTIALLY_FILLED",
    4:"FILLED",5:"CANCELED",6:"EXPIRED",7:"FAILED",
    8:"UNTRIGGERED",9:"TRIGGERED",10:"EXECUTED",
}

class OrderObservationInvalid(ValueError):
    pass

def _event(item, source, block, fills):
    if not isinstance(item,dict):
        raise OrderObservationInvalid("order must be an object")
    for name in ("rq","acc","mkt","st"):
        if type(item.get(name)) is not int or item[name]<0:
            raise OrderObservationInvalid(f"order missing nonnegative {name}")
    if item["st"] not in STATUSES:
        raise OrderObservationInvalid("unsupported order status")
    # Perpl may reject forwarding before assigning an on-chain order id.
    # Only FAILED history records can be accepted without a valid oid.
    oid=item.get("oid")
    if type(oid) is not int or oid<=0:
        if item["st"]==7 and source=="AUTHENTICATED_HISTORY_FIRST_PAGE" and oid in (0,None):
            oid=None
        else:
            raise OrderObservationInvalid("non-failed order requires positive oid")
    for name in ("sr","fr"):
        if name in item and (type(item[name]) is not int or item[name]<0):
            raise OrderObservationInvalid(f"malformed exchange {name}")
    # This is positive evidence of a fill on the first page, not proof of
    # a position (open/close/partial fills have different effects).
    found_fill=any(
        isinstance(f,dict)
        and f.get("acc")==item["acc"]
        and f.get("mkt")==item["mkt"]
        and oid is not None and f.get("oid")==oid
        for f in fills
    )
    return {
        "account_id":item["acc"],"market_id":item["mkt"],
        "request_id":item["rq"],"order_id":oid,
        "status_reason_code":item.get("sr"),
        "failure_reason_code":item.get("fr"),
        "status_code":item["st"],"status":STATUSES[item["st"]],
        "source":source,"snapshot_block":block,
        "fill_found_first_page":found_fill,
        "consequence_verified":False,
        "incident_detected":False,
    }

def summarize_observed_orders(raw,limit=30):
    if type(limit) is not int or not 1<=limit<=100:
        raise OrderObservationInvalid("invalid item limit")
    if not isinstance(raw,dict):
        raise OrderObservationInvalid("missing signed read data")
    w=raw.get("wallet"); o=raw.get("orders"); hist=raw.get("order_history"); fills=raw.get("fills")
    if not isinstance(w,dict) or w.get("mt")!=19 or not isinstance(w.get("as"),list):
        raise OrderObservationInvalid("invalid wallet")
    for label,doc in (("open orders",o),("history",hist),("fills",fills)):
        if not isinstance(doc,dict) or not isinstance(doc.get("d"),list):
            raise OrderObservationInvalid(f"invalid {label} page")
    if o.get("mt")!=23 or not isinstance(hist.get("np",""),str) or not isinstance(fills.get("np",""),str):
        raise OrderObservationInvalid("invalid endpoint schema")
    owned_ids={a.get("id") for a in w["as"] if isinstance(a,dict) and type(a.get("id")) is int}
    def scanned(items,source,block):
        all_count=len(items)
        rows=[]
        for item in items[:limit]:
            e=_event(item,source,block,fills["d"])
            if e["account_id"] not in owned_ids:
                raise OrderObservationInvalid("order account does not match signed wallet")
            rows.append(e)
        return {"available_count":all_count,"shown_count":len(rows),"rows":rows,
                "display_truncated":all_count>limit}
    return {
        "classification":"PERPL_SIGNED_ORDER_OBSERVATIONS",
        "network":"testnet","chain_id":10143,
        "open_orders":scanned(o["d"],"AUTHENTICATED_OPEN_ORDER_SNAPSHOT",o.get("sn")),
        "history_page_1":scanned(hist["d"],"AUTHENTICATED_HISTORY_FIRST_PAGE",None),
        "history_has_more_pages":bool(hist["np"]),
        "fills_first_page_count":len(fills["d"]),
        "fills_has_more_pages":bool(fills["np"]),
        "outcome_certainty":"NO_INCIDENT_INFERRED",
        "empty_history_does_not_prove_absent_execution":True,
        "exchange_writes_enabled":False,
    }
