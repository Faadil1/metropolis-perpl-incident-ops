"""Source-bound negative-path review from signed Perpl Testnet observations.

Output is a READ-only operator review queue, not a diagnosed client bug or a
recovered incident. No action is sent to the exchange.
"""
from __future__ import annotations

REASONS = {
  32: "OrderDescIdTooLow",34: "OrderForwardingNotAllowed",
  36: "OrderPostFailed",23: "MakerOrderSettlementFailed",
  44: "TakerOrderSettlementFailed",
  40: "PriceOutOfRange", 39:"PostOrderUnderMinimum",
  21: "InvalidOrderId", 41:"RecycleBalanceInsufficientSevere",
  46:"UnmatchedLotRemainsInFillOrKill"
}
FAILURE_REASONS={1:"InsufficientBalance",2:"InsufficientCollateralIncrease",
                 3:"InsufficientCollateralInvert",4:"NoPositionToClose",
                 5:"PerpetualSolvency",6:"NegativePositionValue",
                 7:"ReferencePriceStale",8:"ExceedsMaxNegPnlCollat",9:"Other"}

def review_signed_negative_paths(observation):
    result={"classification":"SIGNED_PERPL_NEGATIVE_PATH_REVIEW",
            "source":"AUTHENTICATED_PERPL_TESTNET_SNAPSHOTS_FIRST_PAGE",
            "cases":[],"exchange_writes_enabled":False,
            "incident_recovery_proven":False,
            "actual_live_failure_observed":False,
            "scope":"CURRENT_SIGNED_OBSERVATION_ONLY",
            "no_trading_key_required":True}
    if not isinstance(observation,dict) or observation.get("classification")!="AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW":
        raise ValueError("a validated signed account observation is required")
    observed=observation.get("observed_orders",{})
    if not isinstance(observed,dict) or observed.get("classification")!="PERPL_SIGNED_ORDER_OBSERVATIONS":
        raise ValueError("no matching signed Perpl order observations")
    history=observed.get("history_scan") or observed.get("history_page_1",{})
    if not isinstance(history,dict) or not isinstance(history.get("rows"),list):
        raise ValueError("invalid first-page evidence")
    owned={r.get("account_id"):r for r in observation.get("accounts",[])
           if isinstance(r,dict) and type(r.get("account_id")) is int}
    cases=[]
    seen=set()
    for item in history["rows"]:
        if not isinstance(item,dict) or item.get("source") not in ("AUTHENTICATED_HISTORY_FIRST_PAGE","AUTHENTICATED_SIGNED_HISTORY_PAGINATED"):
            raise ValueError("unsigned or malformed history evidence")
        if item.get("status_code")!=7:
            continue
        acc=item.get("account_id")
        if acc not in owned:
            raise ValueError("failure account outside authenticated owner scope")
        key=(acc,item.get("market_id"),item.get("request_id"),item.get("order_id"))
        if key in seen:continue
        seen.add(key)
        sr=item.get("status_reason_code")
        fr=item.get("failure_reason_code")
        if sr==34:
            instruction=("Check owner intent, current fw permission and API key scope. "
                         "Do NOT enable order forwarding automatically.")
        elif sr==32:
            instruction=("Review account lfr and other active clients. "
                         "Do NOT automatically retry with a fresh rq.")
        else:
            instruction=("Inspect exchange status reason, fills and positions; "
                         "do not infer a safe retry or a completed recovery.")
        cases.append({
          "kind":"POSITIVE_EXCHANGE_FAILURE_EVENT",
          "severity":"REVIEW",
          "account_id":acc,
          "market_id":item["market_id"],
          "original_request_id":item["request_id"],
          "order_id":item.get("order_id"),
          "status":"FAILED",
          "status_reason_code":sr,
          "status_reason":REASONS.get(sr,"UNMAPPED_OR_ABSENT"),
          "failure_reason_code":fr,
          "failure_reason":FAILURE_REASONS.get(fr,"UNMAPPED_OR_ABSENT"),
          "order_forwarding_enabled":owned[acc].get("order_forwarding_enabled"),
          "interpretation":"EXCHANGE_FAILURE_EVENT_NOT_CLIENT_INCIDENT_PROOF",
          "next_step":instruction,
          "retries_authorized":False,
          "exchange_writes_enabled":False,
          "incident_recovery_proven":False,
          "evidence":("PERPL_SIGNED_BOUNDED_HISTORY" if item.get("source")=="AUTHENTICATED_SIGNED_HISTORY_PAGINATED" else "PERPL_SIGNED_FIRST_HISTORY_PAGE"),
        })
    for t in observation.get("order_lifecycle",{}).get("transitions",[]):
        if not isinstance(t,dict):
            continue
        if t.get("finding") not in ("DISAPPEARED_OUTCOME_UNKNOWN","CONFLICTING_TERMINAL_HISTORY_REVIEW"):
            continue
        cases.append({
          "kind":"UNRESOLVED_ORDER_OUTCOME",
          "severity":"HOLD_RECONCILE",
          "account_id":t.get("account_id"),
          "market_id":t.get("market_id"),
          "original_request_id":t.get("request_id"),
          "order_id":t.get("order_id"),
          "interpretation":"UNKNOWN_NOT_FAILED",
          "next_step":("Continue same-scope exchange reconciliation and complete pagination; "
                       "do not resubmit. Warn any actual trading clients; this operator cannot stop external submissions."),
          "retries_authorized":False,
          "exchange_writes_enabled":False,
          "incident_recovery_proven":False,
          "evidence":"LOCAL_COMPARISON_OF_SIGNED_PERPL_OBSERVATIONS",
        })
    result["cases"]=cases
    result["actual_live_failure_observed"]=any(
        c["kind"]=="POSITIVE_EXCHANGE_FAILURE_EVENT" for c in cases)
    result["review_required"]=bool(cases)
    result["first_history_page_incomplete"]=bool(observed.get("history_has_more_pages"))
    result["first_page_history_display_truncated"]=bool(history.get("display_truncated"))
    result["history_pages_scanned"]=history.get("pages_scanned",1)
    result["history_scan_complete"]=history.get("scan_complete",False)
    return result
