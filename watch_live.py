"""Optional Perpl authenticated read-only WebSocket ingestion; no trading calls."""
import argparse, asyncio, json, os, sys
from websockets.asyncio.client import connect
from incident_core import IncidentStore, WS_LIVE
from perpl_client import NETWORKS, PerplReadClient, CredentialsUnavailable

async def watch(store, network='testnet'):
    client=PerplReadClient.from_env(network)
    delay=2
    while True:
        try:
            async with connect(NETWORKS[network]['ws'],open_timeout=9,close_timeout=5,max_size=2_000_000) as ws:
                await ws.send(json.dumps(client.ws_sign_in()))
                delay=2
                async for raw in ws:
                    frame=json.loads(raw)
                    if frame.get('mt') not in (19,23,24,26,100): continue
                    for inc in store.all():
                        if inc['network']==network:
                            store.apply_frame(inc['id'],frame,source=WS_LIVE)
                    if frame.get('mt')==100 and any(i['ws_gap'] for i in store.all()):
                        print('Sequence gap: reconnect and reconcile; do not trade.',flush=True)
                        await ws.close()
                        break
            await asyncio.sleep(2)
        except Exception as exc:
            print(f'WebSocket unavailable ({type(exc).__name__}); read-only retry.',flush=True)
            await asyncio.sleep(delay)
            delay=min(60,delay*2)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--network',choices=['testnet'],default='testnet')
    args=parser.parse_args()
    db=os.environ.get('INCIDENT_DB_PATH',os.path.join(os.path.dirname(__file__),'runtime','incidents.sqlite3'))
    try: asyncio.run(watch(IncidentStore(db),args.network))
    except (CredentialsUnavailable,KeyboardInterrupt) as exc:
        print(f'Watcher stopped: {type(exc).__name__}',file=sys.stderr)
        sys.exit(0 if isinstance(exc,KeyboardInterrupt) else 2)
