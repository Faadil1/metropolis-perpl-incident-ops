# Product Depth & Live Reality — pre-lock

**Status as of 2026-10-10: owner-observed LIVE authenticated reads in the local operator UI; LIVE CORE LOOP = BLOCKED.**

## Required business loop

User/operator creates or detects an uncertain Perpl order → agent/service obtains authenticated exchange state → reconciles request ID, order and position with persisted observations → presents a bounded recovery decision to an authorized operator → performs **only** the explicitly approved safe operation → checks the actual exchange consequence → resolves, escalates or keeps UNKNOWN.

## Verified external public market integration

- 2026-10-10, GitHub Actions public REST checks: **Testnet 10143 = 3/3** and **Mainnet 143 = 3/3** (context, BTC ticker, top-of-book); see run [38066778460](https://github.com/Faadil1/metropolis-perpl-incident-ops/actions/runs/38066778460).
- `POST /api/incidents/{id}/public-market-refresh` now reads the live **testnet** public market state directly from the operator UI, stores local provenance and **does not** change incident/order status.
- Market context is separate from authenticated wallet/order history. The two HTTP snapshots are **not atomic**, even if block numbers match.
- CI market-probe evidence is not authenticated account proof. Later on 2026-10-10, the owner independently used the local operator UI with signed account reads. Incidents and actual recovery remain **BLOCKED**.

## First owner-observed authenticated Testnet milestone — 2026-10-10

**Evidence provenance: USER_REPORTED_SANITIZED_LOCAL_EXECUTION**, not independently authenticated from GitHub runners. The user ran `scripts/verify_perpl_read.ps1` from the cloned repo on Windows and supplied a redacted terminal result:

- **34/34** local regression tests passed.
- `classification = PERPL_TESTNET_AUTHENTICATED_READ`, `chain_id=10143`.
- Five signed GET routes (wallet, open orders, positions, order history, fills) each returned **HTTP 200**.
- 0 open orders, 0 open positions, 0 first-page history events and 0 fills.
- `exchange_writes_enabled = false`, `authenticated_core_loop_proven = false`.
- No API token, Ed25519 secret, wallet address, balances or account id were published or recorded in this repo.

These signed API responses **prove connectivity to a real Perpl Testnet account at the user-reported execution time**. They do not prove testnet order placement, genuine incident observation, safe intervention, recovery or customer demand. The exact scope of the issued key is not cryptographically attested by the HTTP 200 reads.

**Second observed milestone — user screenshot from the actual operator UI (`127.0.0.1:8765`):**
- UI label: `SIGNED PERPL GET / TESTNET / LIVE ACCOUNT SNAPSHOTS`.
- Read blocks: wallet **69,883,405**; orders **69,883,406**; positions **69,883,407**. They are deliberately **non-atomic HTTP snapshots**.
- First-page order history and fills were empty; `exchange_writes_enabled=false`, `incident_recovery_proven=false`, `live_core_loop_proven=false`.
- **Evidence boundary:** the screenshot is owner-supplied; we did not independently retrieve authenticated data or receive secrets. The screenshot itself has not been uploaded into the public repository. The screenshot does not show the entire JSON, and no unshown values are inferred.
- **Verdict:** `AUTHENTICATED_OPERATOR_READ = PROVEN (owner screenshot)`; `LIVE_CORE_LOOP = BLOCKED`.

Next: observe a subsequent genuine account change via READ (no trading required for the application to function), classify changes only as **investigate**, then verify real order and response evidence before proposing any action. No auto-created fake incidents or unapproved exchange writes.

## Second operator LIVE read — 2026-10-10

The owner sent a screenshot of the updated local application showing **1 authenticated Perpl exchange account (#1060)**, **0 open orders, 0 open positions, 0 first-page order-history entries and 0 fills**. The visible account flags are **NOT FROZEN** and **ORDER FORWARDING OFF**.

The UI reports **NO CHANGE OBSERVED IN THESE AGGREGATES**, with wallet/orders/positions blocks **69893555/69893556/69893557**. This is a second real signed snapshot comparison (user screenshot evidence); it does **not** establish absence of unknown order outcomes, nor a complete incident/recovery loop.

The owner screenshot is **not** uploaded to public GitHub; only the sanitized non-secret statement is included. No exchange writes or fake incidents were carried out.

A further product increment implements sanitized **real order observations** from the authenticated open-order snapshot and first order-history page. When the account is empty the product must show no observed orders. It must not manufacture order IDs, infer errors from missing rows, or claim a recovered incident. Later live orders must be user-observed before promotion.

## Evidence boundaries

| Claim | State |
|---|---|
| Perpl REST/WS schema code and local API behavior | LOCAL_VERIFIED |
| Public Perpl Testnet + Mainnet context/ticker/book through GitHub runner | LIVE_PUBLIC_OBSERVED (external probe only) |
| Public Perpl Testnet market data in operator UI | IMPLEMENTED, not externally exercised |
| Published Desk false-expiry incident | EXTERNAL_DOCUMENTED_HISTORICAL |
| Read access to user's actual testnet Perpl account | **PROVEN by user-provided sanitized 5/5 HTTP 200 run** |
| Authenticated account overview inside operator UI | **PROVEN by owner screenshot (local UI + real Perpl signed GET)** |
| Two signed account reads compared in UI, no aggregate change | **PROVEN by second owner screenshot** |
| Real order details observed inside product | **NOT YET PROVEN** (0 live orders/history) |
| Received order-status event from live Perpl WS | BLOCKED |
| Approved and executed a testnet cancel | NOT_IMPLEMENTED |
| Final position/order consequence reconciled | NOT_IMPLEMENTED |
| Owner/operator exercised authenticated account-read UI | **PROVEN by screenshot** |
| Independent third-party operator using full incident/recovery workflow | UNKNOWN |
| Live user value, paid intent, repeat use | UNKNOWN |

## Scenarios for product depth

Success: order known open → validated fresh snapshot → owner approval → cancel action → exchange status and position verified.

Negative: ACK missing but actual fill present → never resend with a new request ID; hold, reconcile and update state.

Boundary: seq gap; partial fills; duplicate `mt:24`; contradictory exchange events; multi-client `rq`; rate limits.

Recovery: restart durable incident store, reconnect socket and re-anchor `sn`, restore latest verified state, escalate UNKNOWN, avoid duplicate writes.

Operator/user workflow: search, classify, compare current vs previous, authorize only bounded recovery, reverse or replan when valid.

**No replay, seed, screenshots or local tests can complete the live loop.** After the first genuine live operation, continue the product exploitation loop while justified by actual operator value; don't stop at a single vertical slice.
