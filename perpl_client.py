"""Perpl signed read-only testnet client; deliberately no POST or trade scope."""
from __future__ import annotations
import base64, hashlib, os, secrets, time
from urllib.parse import urlencode, urlsplit, parse_qsl
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import httpx

NETWORKS = {
    'testnet': {'chain_id':10143,'api':'https://testnet.perpl.xyz/api','ws':'wss://testnet.perpl.xyz/ws/v1/trading'},
    'mainnet': {'chain_id':143,'api':'https://app.perpl.xyz/api','ws':'wss://app.perpl.xyz/ws/v1/trading'}
}
READ_TARGETS={'wallet':'/v1/trading/wallet','orders':'/v1/trading/orders','positions':'/v1/trading/positions',
              'order_history':'/v1/trading/order-history?count=100',
              'fills':'/v1/trading/fills?count=100'}

class CredentialsUnavailable(RuntimeError): pass

@dataclass(frozen=True)
class PerplReadClient:
    network:str
    api_key:str
    private_key:Ed25519PrivateKey

    @classmethod
    def from_env(cls,network:str):
        if network!='testnet': raise ValueError('only testnet authenticated reads permitted')
        key=os.environ.get('PERPL_API_KEY_READ','').strip()
        secret=os.environ.get('PERPL_API_KEY_SECRET_READ','').strip().removeprefix('0x')
        if not key or not secret: raise CredentialsUnavailable('testnet read credentials missing in env')
        try:
            raw=bytes.fromhex(secret)
            if len(raw)!=32: raise ValueError('must be 32 bytes')
            signing_key=Ed25519PrivateKey.from_private_bytes(raw)
        except ValueError as exc: raise CredentialsUnavailable('bad Ed25519 read-key format') from exc
        return cls(network,key,signing_key)

    def _sig(self,canonical:str):
        return base64.urlsafe_b64encode(self.private_key.sign(canonical.encode())).decode().rstrip('=')

    def _nonce(self):
        return base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip('=')

    @staticmethod
    def history_target(label, cursor):
        if label not in ("order_history","fills") or not isinstance(cursor,str):
            raise ValueError("invalid history scan")
        if not cursor or len(cursor)>256 or any(ord(ch)<33 or ord(ch)>126 for ch in cursor):
            raise ValueError("invalid pagination cursor")
        path="/v1/trading/order-history" if label=="order_history" else "/v1/trading/fills"
        return path+"?"+urlencode({"count":"100","page":cursor})

    def signed_get_headers(self,target:str,timestamp_ms:int|None=None,nonce:str|None=None):
        if target not in READ_TARGETS.values():
            parsed=urlsplit(target)
            valid_path=parsed.path in ("/v1/trading/order-history","/v1/trading/fills")
            try:
                params=parse_qsl(parsed.query,keep_blank_values=True,strict_parsing=True)
                match=(valid_path and not parsed.scheme and not parsed.netloc and
                       not parsed.fragment and len(params)==2 and
                       params[0]==("count","100") and params[1][0]=="page")
                if match:
                    label="order_history" if parsed.path.endswith("order-history") else "fills"
                    match=target==self.history_target(label,params[1][1])
            except ValueError:
                match=False
            if not match:
                raise ValueError("not read-only allowlisted endpoint")
        ts=str(int(time.time()*1000) if timestamp_ms is None else timestamp_ms)
        n=nonce or self._nonce()
        canonical='\n'.join([str(NETWORKS[self.network]['chain_id']),'GET',target,ts,n,hashlib.sha256(b'').hexdigest()])
        return {'X-API-Key':self.api_key,'X-API-Timestamp':ts,'X-API-Nonce':n,'X-API-Signature':self._sig(canonical),'Accept':'application/json'}

    def ws_sign_in(self):
        ts=str(int(time.time()*1000)); nonce=self._nonce()
        canonical='\n'.join([str(NETWORKS[self.network]['chain_id']),'trading-ws-signin',ts,nonce])
        return {'mt':29,'chain_id':NETWORKS[self.network]['chain_id'],'api_key':self.api_key,'timestamp':ts,'nonce':nonce,'signature':self._sig(canonical)}

    def public_context(self,timeout=8.0,transport=None):
        with httpx.Client(timeout=timeout,follow_redirects=False,transport=transport) as client:
            res=client.get(NETWORKS[self.network]['api']+'/v1/pub/context')
            res.raise_for_status(); doc=res.json()
            if not isinstance(doc,dict) or not isinstance(doc.get('markets'),list) or doc.get('chain',{}).get('chain_id')!=NETWORKS[self.network]['chain_id']:
                raise ValueError('unexpected chain or market context')
            return doc

    def read_all(self,timeout=9.0,transport=None,max_history_pages=5):
        if type(max_history_pages) is not int or not 1<=max_history_pages<=10:
            raise ValueError("max_history_pages must be 1..10")
        out={}
        with httpx.Client(timeout=timeout,follow_redirects=False,transport=transport) as client:
            for label,target in READ_TARGETS.items():
                try:
                    res=client.get(NETWORKS[self.network]['api']+target,headers=self.signed_get_headers(target))
                    res.raise_for_status(); doc=res.json()
                    if label in ('wallet','orders','positions'):
                        if not isinstance(doc,dict) or doc.get('mt')!={'wallet':19,'orders':23,'positions':26}[label]:
                            raise ValueError('unexpected snapshot type')
                    elif not isinstance(doc,dict) or not isinstance(doc.get('d'),list) or not isinstance(doc.get('np',''),str):
                        raise ValueError('unexpected history page type; cannot infer order outcome')
                    out[label]=doc
                    if label in ("order_history","fills"):
                        pages=[doc]
                        cursor=doc["np"]
                        visited=set()
                        while cursor and len(pages)<max_history_pages:
                            if cursor in visited:
                                raise ValueError("repeated exchange history cursor")
                            visited.add(cursor)
                            paged_target=self.history_target(label,cursor)
                            nxt=client.get(NETWORKS[self.network]["api"]+paged_target,
                                headers=self.signed_get_headers(paged_target))
                            nxt.raise_for_status()
                            page=nxt.json()
                            if not isinstance(page,dict) or not isinstance(page.get("d"),list) or not isinstance(page.get("np",""),str):
                                raise ValueError("invalid signed history page")
                            pages.append(page)
                            cursor=page["np"]
                        out[label+"_scan"]={
                            "source":"BOUNDED_SIGNED_PERPL_HISTORY_GET",
                            "pages":pages,
                            "page_count":len(pages),
                            "complete":not bool(cursor),
                            "more_pages_unread":bool(cursor)}
                except (httpx.HTTPError,ValueError) as exc:
                    raise ConnectionError(f'{label} read failed ({type(exc).__name__}); outcome UNKNOWN') from None
        return out
