"""Perpl signed read-only testnet client; deliberately no POST or trade scope."""
from __future__ import annotations
import base64, hashlib, os, secrets, time
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import httpx

NETWORKS = {
    'testnet': {'chain_id':10143,'api':'https://testnet.perpl.xyz/api','ws':'wss://testnet.perpl.xyz/ws/v1/trading'},
    'mainnet': {'chain_id':143,'api':'https://app.perpl.xyz/api','ws':'wss://app.perpl.xyz/ws/v1/trading'}
}
READ_TARGETS={'wallet':'/v1/trading/wallet','orders':'/v1/trading/orders','positions':'/v1/trading/positions'}

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

    def signed_get_headers(self,target:str,timestamp_ms:int|None=None,nonce:str|None=None):
        if target not in READ_TARGETS.values(): raise ValueError('not read-only allowlisted endpoint')
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

    def read_all(self,timeout=9.0,transport=None):
        out={}
        with httpx.Client(timeout=timeout,follow_redirects=False,transport=transport) as client:
            for label,target in READ_TARGETS.items():
                try:
                    res=client.get(NETWORKS[self.network]['api']+target,headers=self.signed_get_headers(target))
                    res.raise_for_status(); doc=res.json()
                    if not isinstance(doc,dict) or doc.get('mt')!={'wallet':19,'orders':23,'positions':26}[label]:
                        raise ValueError('unexpected snapshot type')
                    out[label]=doc
                except (httpx.HTTPError,ValueError) as exc:
                    raise ConnectionError(f'{label} read failed ({type(exc).__name__}); outcome UNKNOWN') from None
        return out
