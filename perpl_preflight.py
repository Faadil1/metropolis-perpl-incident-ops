"""Safe public Perpl context preflight; no auth, orders or deposits."""
import argparse, json, pathlib, time, urllib.error, urllib.request
ENDPOINTS={'testnet':('https://testnet.perpl.xyz/api/v1/pub/context',10143),
           'mainnet':('https://app.perpl.xyz/api/v1/pub/context',143)}
def check(network, timeout=8):
    url,expected=ENDPOINTS[network]
    result={'checked_at_ms':int(time.time()*1000),'network':network,
            'url':url,'status':'UNKNOWN','live_core_loop_proven':False}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Metropolis-Perpl-Read-Preflight/0.1'})
        with urllib.request.urlopen(req,timeout=timeout) as response:
            doc=json.load(response)
        observed=doc.get('chain',{}).get('chain_id') if isinstance(doc,dict) else None
        markets=doc.get('markets') if isinstance(doc,dict) else None
        result.update({'observed_chain_id':observed,'market_count':len(markets) if isinstance(markets,list) else None,
                       'status':'PUBLIC_CONTEXT_OBSERVED' if observed==expected and isinstance(markets,list) else 'SCHEMA_OR_CHAIN_MISMATCH'})
    except (urllib.error.URLError,TimeoutError,ValueError,OSError) as exc:
        result.update({'status':'PUBLIC_READ_UNAVAILABLE','error_kind':type(exc).__name__})
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--network',choices=ENDPOINTS,default='testnet')
    p.add_argument('--output',default='runtime/public_preflight.json')
    args=p.parse_args()
    result=check(args.network)
    out=pathlib.Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PUBLIC_CONTEXT_OBSERVED' else 2)
