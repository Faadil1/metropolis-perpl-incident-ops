"""Real public Perpl market context for the operator workflow.

Uses fixed TESTNET public endpoints. Never supplies account, wallet or order outcome.
Ticker and book are different HTTP snapshots: not atomic.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import httpx

BASE="https://testnet.perpl.xyz/api"
CHAIN_ID=10143

class PublicMarketUnavailable(RuntimeError):
    pass

@dataclass(frozen=True)
class PublicMarketReader:
    timeout:float=7.5
    transport:object|None=None

    def refresh(self,market_id:int):
        if type(market_id) is not int or market_id<0:
            raise ValueError('market id must be nonnegative integer')
        try:
            with httpx.Client(timeout=self.timeout,follow_redirects=False,transport=self.transport) as client:
                def fetch(route):
                    response=client.get(BASE+route,headers={'Accept':'application/json'})
                    response.raise_for_status()
                    doc=response.json()
                    if not isinstance(doc,dict): raise ValueError('expected JSON object')
                    return doc
                ctx=fetch('/v1/pub/context')
                if ctx.get('chain',{}).get('chain_id')!=CHAIN_ID:
                    raise ValueError('testnet chain id mismatch')
                markets=ctx.get('markets')
                if not isinstance(markets,list): raise ValueError('invalid context markets')
                m=next((x for x in markets if isinstance(x,dict) and x.get('id')==market_id),None)
                if m is None: raise ValueError('market id absent from live context')
                ticker=fetch(f'/v1/market-data/{market_id}/ticker')
                book=fetch(f'/v1/market-data/{market_id}/book?levels=10')
        except (httpx.HTTPError,ValueError,TypeError) as exc:
            raise PublicMarketUnavailable(f'public market read unverified: {type(exc).__name__}') from None

        # Ticker and book can have different block heights: do not claim an atomic snapshot.
        state=ticker.get('d',{}).get(str(market_id)) if isinstance(ticker.get('d'),dict) else None
        if (ticker.get('mt')!=9 or not isinstance(state,dict) or
            book.get('mt')!=15 or not isinstance(book.get('bid'),list) or
            not isinstance(book.get('ask'),list)):
            raise PublicMarketUnavailable('unexpected ticker/book schema')
        pd=m.get('config',{}).get('price_decimals')
        if type(pd) is not int or not (0<=pd<=20):
            raise PublicMarketUnavailable('market price decimal precision unknown')
        def price(raw):
            return raw/(10**pd) if type(raw) is int else None
        tb=state.get('at',{}).get('b')
        bb=book.get('at',{}).get('b')
        bid=book['bid'][0] if book['bid'] and isinstance(book['bid'][0],dict) else {}
        ask=book['ask'][0] if book['ask'] and isinstance(book['ask'][0],dict) else {}
        return {
            'classification':'LIVE_PUBLIC_MARKET_DATA_ONLY',
            'does_not_prove_order_or_position':True,
            'network':'testnet',
            'chain_id':CHAIN_ID,
            'market_id':market_id,
            'symbol':m.get('symbol'),
            'price_decimals':pd,
            'mark_price':price(state.get('mrk')),
            'top_bid':price(bid.get('p')),
            'top_ask':price(ask.get('p')),
            'ticker_block':tb,
            'book_block':bb,
            'non_atomic_http_reads':True,
            'same_block_observed':type(tb) is int and type(bb) is int and tb==bb,
            'retrieved_at':datetime.now(timezone.utc).isoformat(),
        }
