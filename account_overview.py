"""Sanitized authenticated Perpl account overview.

Produces no wallet address, collateral balances, order details or credentials.
The observation is LIVE only when sourced from signed Perpl GET requests.
"""
from __future__ import annotations
from datetime import datetime, timezone

class AccountOverviewInvalid(ValueError): pass

def from_signed_snapshots(data):
    if not isinstance(data,dict):
        raise AccountOverviewInvalid("missing signed snapshots")
    w=data.get('wallet')
    if not isinstance(w,dict) or w.get('mt')!=19 or not isinstance(w.get('as'),list):
        raise AccountOverviewInvalid("expected WalletSnapshot mt=19 with as[]")
    rows=[]
    for a in w['as']:
        if not isinstance(a,dict) or type(a.get('id')) is not int or type(a.get('in')) is not int:
            raise AccountOverviewInvalid("account record lacks id or instance")
        if type(a.get('fw')) is not bool or type(a.get('fr')) is not bool:
            raise AccountOverviewInvalid("account requires boolean forwarding/frozen state")
        n=a.get('lfr')
        if type(n) is not int or n<0:
            raise AccountOverviewInvalid("missing account lfr")
        rows.append({"account_id":a['id'],"instance_id":a['in'],
                     "order_forwarding_enabled":a['fw'],"frozen":a['fr'],
                     "last_forwarded_request_id":n})
    counts={}
    block={}
    for label,mt in (('orders',23),('positions',26)):
        item=data.get(label)
        if not isinstance(item,dict) or item.get('mt')!=mt or not isinstance(item.get('d'),list):
            raise AccountOverviewInvalid(f"invalid {label} snapshot")
        block[label]=item.get('sn')
        counts[label]=len(item['d'])
    block['wallet']=w.get('sn')
    pages={}
    for label in ('order_history','fills'):
        item=data.get(label)
        if not isinstance(item,dict) or not isinstance(item.get('d'),list) or not isinstance(item.get('np',''),str):
            raise AccountOverviewInvalid(f"invalid {label} history")
        pages[label]={'first_page_count':len(item['d']),
                      'has_more_pages':bool(item.get('np'))}
    return {
        "classification":"AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW",
        "chain_id":10143, "source":"SIGNED_PERPL_HTTP_GET",
        "retrieved_at":datetime.now(timezone.utc).isoformat(),
        "accounts":rows,
        "open_orders_count":counts['orders'],
        "open_positions_count":counts['positions'],
        "history":pages,
        "snapshot_blocks":block,
        "non_atomic_http_reads":True,
        "exchange_writes_enabled":False,
        "incident_recovery_proven":False,
        "live_core_loop_proven":False,
        "note":"Empty first-page history cannot prove an order never executed",
    }
