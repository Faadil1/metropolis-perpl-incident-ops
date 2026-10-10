# Product Depth & Live Reality — pre-lock

**Status as of 2026-10-10: LOCAL_VERIFIED; LIVE CORE LOOP = BLOCKED.**

## Required business loop

User/operator creates or detects an uncertain Perpl order → agent/service obtains authenticated exchange state → reconciles request ID, order and position with persisted observations → presents a bounded recovery decision to an authorized operator → performs **only** the explicitly approved safe operation → checks the actual exchange consequence → resolves, escalates or keeps UNKNOWN.

## Verified external public market integration

- 2026-10-10, GitHub Actions public REST checks: **Testnet 10143 = 3/3** and **Mainnet 143 = 3/3** (context, BTC ticker, top-of-book); see run [38066778460](https://github.com/Faadil1/metropolis-perpl-incident-ops/actions/runs/38066778460).
- `POST /api/incidents/{id}/public-market-refresh` now reads the live **testnet** public market state directly from the operator UI, stores local provenance and **does not** change incident/order status.
- Market context is separate from authenticated wallet/order history. The two HTTP snapshots are **not atomic**, even if block numbers match.
- CI verification is a live source probe, not evidence that an external user used the app. Authentic account reads, incidents and actual recovery remain **BLOCKED**.

## Evidence boundaries

| Claim | State |
|---|---|
| Perpl REST/WS schema code and local API behavior | LOCAL_VERIFIED |
| Public Perpl Testnet + Mainnet context/ticker/book through GitHub runner | LIVE_PUBLIC_OBSERVED (external probe only) |
| Public Perpl Testnet market data in operator UI | IMPLEMENTED, not externally exercised |
| Published Desk false-expiry incident | EXTERNAL_DOCUMENTED_HISTORICAL |
| Read access to user's actual testnet Perpl account | BLOCKED |
| Received order-status event from live Perpl WS | BLOCKED |
| Approved and executed a testnet cancel | NOT_IMPLEMENTED |
| Final position/order consequence reconciled | NOT_IMPLEMENTED |
| Real external operator using the workflow | UNKNOWN |
| Live user value, paid intent, repeat use | UNKNOWN |

## Scenarios for product depth

Success: order known open → validated fresh snapshot → owner approval → cancel action → exchange status and position verified.

Negative: ACK missing but actual fill present → never resend with a new request ID; hold, reconcile and update state.

Boundary: seq gap; partial fills; duplicate `mt:24`; contradictory exchange events; multi-client `rq`; rate limits.

Recovery: restart durable incident store, reconnect socket and re-anchor `sn`, restore latest verified state, escalate UNKNOWN, avoid duplicate writes.

Operator/user workflow: search, classify, compare current vs previous, authorize only bounded recovery, reverse or replan when valid.

**No replay, seed, screenshots or local tests can complete the live loop.** After the first genuine live operation, continue the product exploitation loop while justified by actual operator value; don't stop at a single vertical slice.
