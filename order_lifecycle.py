"""Read-only lifecycle evidence from two signed Perpl account observations.

A missing order is UNKNOWN until a positive matching exchange history status
is observed. A normal cancel is not an incident recovery.
"""
from __future__ import annotations

def _ident(row):
    return tuple(row[k] for k in ("account_id","market_id","request_id","order_id"))

def compare_order_lifecycle(previous, current):
    result={
        "classification":"NO_ORDER_TRANSITIONS_PROVEN",
        "transitions":[],
        "incident_recovery_proven":False,
        "position_consequence_verified":False,
        "exchange_writes_enabled":False,
    }
    if not isinstance(previous,dict) or not isinstance(current,dict):
        return result
    if (previous.get("classification")!="AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW"
        or current.get("classification")!="AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW"):
        return result
    p=previous.get("observed_orders"); n=current.get("observed_orders")
    if not isinstance(p,dict) or not isinstance(n,dict):
        return {**result,"classification":"ORDER_ROW_EVIDENCE_MISSING"}
    old_open=p.get("open_orders",{})
    now_open=n.get("open_orders",{})
    history=n.get("history_page_1",{})
    if not all(isinstance(doc,dict) and isinstance(doc.get("rows"),list)
               for doc in (old_open,now_open,history)):
        return {**result,"classification":"ORDER_ROW_EVIDENCE_MISSING"}
    prev_accounts={(r.get("instance_id"),r.get("account_id")) for r in previous.get("accounts",[])}
    now_accounts={(r.get("instance_id"),r.get("account_id")) for r in current.get("accounts",[])}
    if prev_accounts!=now_accounts:
        return {**result,"classification":"ACCOUNT_REBASE_REQUIRED"}
    if (old_open.get("display_truncated") or now_open.get("display_truncated")):
        return {**result,"classification":"ORDER_ROWS_TRUNCATED_CANNOT_COMPARE"}
    now_keys={_ident(r) for r in now_open["rows"]}
    history_by_key={}
    for r in history["rows"]:
        history_by_key.setdefault(_ident(r),set()).add(r.get("status_code"))
    transitions=[]
    for old in old_open["rows"]:
        if old.get("status") not in ("OPEN","PARTIALLY_FILLED","UNTRIGGERED"):
            continue
        k=_ident(old)
        if k in now_keys:
            continue
        statuses=history_by_key.get(k,set())
        if 4 in statuses and 5 in statuses:
            finding="CONFLICTING_FILLED_AND_CANCELED_HISTORY"
        elif 5 in statuses:
            finding="CANCELED_STATUS_OBSERVED"
        elif 4 in statuses:
            finding="FILLED_STATUS_OBSERVED"
        elif 6 in statuses:
            finding="EXPIRED_STATUS_OBSERVED"
        elif 7 in statuses:
            finding="FAILED_STATUS_OBSERVED"
        else:
            finding="DISAPPEARED_OUTCOME_UNKNOWN"
        transitions.append({
            "account_id":k[0],"market_id":k[1],"request_id":k[2],"order_id":k[3],
            "previous_status":old["status"],"finding":finding,
            "positive_matching_history":finding not in ("DISAPPEARED_OUTCOME_UNKNOWN",),
            "position_consequence_verified":False,
            "incident_recovery_proven":False,
            "history_first_page_only":True,
        })
    classification=("ORDER_LIFECYCLE_REVIEW_REQUIRED" if transitions
                    else "NO_ORDER_TRANSITIONS_PROVEN")
    return {**result,"classification":classification,"transitions":transitions}
