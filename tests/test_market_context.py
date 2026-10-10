"""Live public market integration is never a source of order/execution truth."""
import pytest
import httpx
from perpl_market import PublicMarketReader, PublicMarketUnavailable

def market_transport(chain=10143, same_block=False):
    def handle(req):
        path=req.url.path
        if path.endswith('/v1/pub/context'):
            return httpx.Response(200,json={
                'chain':{'chain_id':chain},
                'markets':[{'id':16,'symbol':'BTC-PERP','config':{'price_decimals':1}}]})
        if path.endswith('/ticker'):
            return httpx.Response(200,json={
                'mt':9,'sn':103,'d':{'16':{'at':{'b':103},'mrk':1005000}}})
        if path.endswith('/book'):
            return httpx.Response(200,json={
                'mt':15,'sn':(103 if same_block else 102),'at':{'b':(103 if same_block else 102)},
                'bid':[{'p':1004990,'s':3,'o':1}],
                'ask':[{'p':1005010,'s':1,'o':1}]})
        raise AssertionError(f'unexpected route: {path}')
    return httpx.MockTransport(handle)

def test_public_market_usable_live_surface_with_provenance():
    doc=PublicMarketReader(transport=market_transport()).refresh(16)
    assert doc['classification']=='LIVE_PUBLIC_MARKET_DATA_ONLY'
    assert doc['mark_price']==100500
    assert doc['top_bid']==100499
    assert doc['same_block_observed'] is False
    assert doc['does_not_prove_order_or_position'] is True

def test_block_match_does_not_make_reads_atomic():
    doc=PublicMarketReader(transport=market_transport(same_block=True)).refresh(16)
    assert doc['same_block_observed'] is True
    assert doc['non_atomic_http_reads'] is True

def test_chain_mismatch_rejected():
    with pytest.raises(PublicMarketUnavailable):
        PublicMarketReader(transport=market_transport(chain=143)).refresh(16)

def test_unknown_market_refused():
    with pytest.raises(PublicMarketUnavailable):
        PublicMarketReader(transport=market_transport()).refresh(999)

def test_http_failure_keeps_unknown():
    def fail(req):
        return httpx.Response(503,json={'error':'not ready'})
    with pytest.raises(PublicMarketUnavailable):
        PublicMarketReader(transport=httpx.MockTransport(fail)).refresh(16)
