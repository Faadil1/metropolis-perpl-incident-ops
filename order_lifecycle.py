"""Reconcile a Perpl order across signed snapshots and genuine exchange actions.

Perpl cancellation is a NEW command with its own rq but references the ORIGINAL
order via oid. A cancellation status can thus have a different rq. Evidence of
a normal cancellation is not proof of a recovered incident.
"""
from __future__ import annotations

def _order_key(row):
    return (row.get("account_id"),row.get("market_id"),row.get("order_id"))

def _scope(snapshot):
    return {(a.get("instance_id"),a.get("account_id"))
            for a in snapshot.get("accounts",[]) if isinstance(a,dict)}

def _rows(snapshot,label):
    obj=snapshot.get("observed_orders",{}).get(label,{})
    if not isinstance(obj,dict) or not isinstance(obj.get("rows"),list):
        return None
    return obj

def compare_order_lifecycle(previous,current,earlier=()):
    base={"classification":"NO_ORDER_TRANSITIONS_PROVEN","transitions":[],
          "incident_recovery_proven":False,
          "position_consequence_verified":False,
          "exchange_writes_enabled":False}
    if not isinstance(current,dict) or current.get("classification")!="AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW":
        return base
    here=_rows(current,"open_orders");history=_rows(current,"history_scan") or _rows(current,"history_page_1")
    if here is None or history is None:
        return {**base,"classification":"ORDER_ROW_EVIDENCE_MISSING"}
    if here.get("display_truncated"):
        return {**base,"classification":"ORDER_ROWS_TRUNCATED_CANNOT_COMPARE"}

    candidates=([previous] if isinstance(previous,dict) else [])+list(earlier)
    # All candidate evidence must have identical owned account+instance scope.
    scope=_scope(current)
    previously={}
    any_verified=False
    for doc in candidates:
        if not isinstance(doc,dict) or doc.get("classification")!="AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW":
            continue
        if _scope(doc)!=scope:
            continue
        rows=_rows(doc,"open_orders")
        if rows is None or rows.get("display_truncated"):
            continue
        any_verified=True
        for row in rows["rows"]:
            if not isinstance(row,dict) or row.get("status") not in ("OPEN","PARTIALLY_FILLED","UNTRIGGERED"):
                continue
            key=_order_key(row)
            if not all(type(p) is int for p in key) or type(row.get("request_id")) is not int:
                continue
            previously.setdefault(key,{"row":row,"observed_at":doc.get("retrieved_at")})
    if not any_verified:
        return {**base,"classification":"BASELINE_ORDER_HISTORY_UNAVAILABLE"}
    active_keys={_order_key(r) for r in here["rows"] if isinstance(r,dict)}
    history_by_key={}
    for event in history["rows"]:
        if isinstance(event,dict):
            history_by_key.setdefault(_order_key(event),[]).append(event)

    transitions=[]
    for key,prior in previously.items():
        if key in active_keys:
            continue
        events=history_by_key.get(key,[])
        terminal=[e for e in events if e.get("status_code") in (4,5,6,7,10)]
        terminal_codes={e["status_code"] for e in terminal}
        if len(terminal_codes)>1:
            finding="CONFLICTING_TERMINAL_HISTORY_REVIEW"
            selected=None
        elif terminal:
            selected=terminal[0]
            finding={4:"FILLED_STATUS_OBSERVED",5:"CANCELED_STATUS_OBSERVED",
                     6:"EXPIRED_STATUS_OBSERVED",7:"FAILED_STATUS_OBSERVED",
                     10:"EXECUTED_STATUS_OBSERVED"}[selected["status_code"]]
        else:
            selected=None
            finding="DISAPPEARED_OUTCOME_UNKNOWN"
        transitions.append({
            "account_id":key[0],"market_id":key[1],"order_id":key[2],
            "request_id":prior["row"]["request_id"],
            "terminal_event_request_id":selected.get("request_id") if selected else None,
            "request_id_changed_on_terminal_action":(
                selected is not None and selected.get("request_id")!=prior["row"]["request_id"]),
            "previous_status":prior["row"]["status"],
            "previously_observed_at":prior["observed_at"],
            "finding":finding,
            "positive_matching_history":selected is not None,
            "history_first_page_only":history.get("pages_scanned",1)==1,
            "history_scan_complete":history.get("scan_complete",False),
            "first_page_fill_for_order_observed":any(bool(e.get("fill_found_first_page")) for e in events),
            "position_consequence_verified":False,
            "incident_recovery_proven":False
        })
    return {**base,"classification":("ORDER_LIFECYCLE_REVIEW_REQUIRED" if transitions else
                                     "NO_ORDER_TRANSITIONS_PROVEN"),
            "transitions":transitions}
