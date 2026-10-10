# First real Perpl Testnet order — authenticated identity correlation

**2026-10-10 — owner-supplied screenshot of the local operator**, not a generated test fixture.

- Exchange: Perpl, **Monad Testnet 10143**.
- Account **1060**, market **16 (BTC)**, real order status **OPEN**.
- Request ID (`rq`) and order ID (`oid`) were present as matching fields in **both** signed-open-order and first-page signed-history views.
- Instead of publicizing the owner's exact order IDs, this receipt stores a SHA-256 commitment of the pipe-delimited tuple `10143|account_id|market_id|rq|oid`: `b90a6004e8389540821a673d89292d60449da3cdff808c70173712869da7a0aa`. The commitment can later be matched against the owner-held screenshot.
- Signed GET blocks: **wallet 69901506**, **open orders 69901507**, **positions 69901507**.
- The history event reported **OPEN**, not CANCELED; first-page fills **0**, open positions **0**.
- Aggregate `NO_CHANGE_OBSERVED` describes only the newest two reads and is consistent with an order staying OPEN; an earlier owner screenshot established 0→1.
- The screenshots themselves were not added to public GitHub and no API or signing keys were received.

**Verdict:** real `rq+oid` exchange identity correlation = **PROVEN from owner-observed localhost screen**. A negative event, cancellation, fill reconciliation, price risk consequence, or actual incident recovery = **NOT PROVEN**.

**Next step:** on official Perpl Testnet UI cancel this exact open order once, then refresh the read-only operator app and verify a positive matching `CANCELED` history event with no active matching open row. A disappearance by itself remains UNKNOWN.
