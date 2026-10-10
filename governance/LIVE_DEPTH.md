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

## First genuine user-owned Perpl Testnet order and Metropolis detection — 2026-10-10

**Two independent owner-provided screenshots, different surfaces:**

- **Official Perpl Testnet UI:** account #1060, `BTC PERP`, **Limit / Long / Post Only / 1×**, price **82,000 USD**, size **0.0002 BTC**, notional **16.40 test USD**, status **OPEN**, remaining size **0.0002 BTC**. Open orders tab displayed one row; no trade execution visible in that row. These figures are an owner screenshot of a live testnet order, not replay.
- **Actual local Metropolis UI:** authenticated signed Testnet GET shows **1 open order** (previously 0), **1 first-page history event**, **0 fills**, **0 open positions**, and `ACTIVITY_CHANGE_REVIEW_ONLY`. Snapshot blocks: wallet **69,900,670**, open orders **69,900,671**, positions **69,900,672** (non-atomic HTTP). No incident was created, no exchange write made.
- **Strict evidence boundary:** live count change is proven. The local screenshot does *not* show the new `Ordres réellement observés` panel, so `rq`, `oid`, provenance of the specific row and exact account-order matching in that code path remain **NOT YET USER-VERIFIED**. Do not invent IDs or claim incident resolution. The displayed UI appears to be an older locally running server; restart after pulling the latest research branch.
- Pending order can fill while testnet market moves; never promise it will remain open. Owner may cancel independently via Perpl if unwilling to retain an open order. Read-only app has no cancel ability.
- Screenshots and private API material are **not** published to public GitHub. Only these sanitized operator-supplied observations are retained.

**Verified:** a real exchange order exists and the signed local operator monitor detects changed aggregate order count (LIVE positive path). **Not verified:** detailed row mapping, reliable negative-event detection, safe exchange intervention, recovery, competitive differentiated value, full product depth and Concept Lock.

## Order identity and read-only cancellation-reconciliation readiness — 2026-10-10

Owner provided a screenshot of the latest local Metropolis UI. **A genuine Perpl Testnet open order is now matched across the signed open-order snapshot and order-history first page** using identical `account_id + market_id + rq + oid`:

- Network **Monad Testnet (10143)**, account **1060**, BTC market **16**.
- Exact `rq` and `oid` are visible in the private owner screenshot but **not published verbatim** in this public repo. Canonical digest of `10143|account_id|market_id|rq|oid`, SHA-256: `b90a6004e8389540821a673d89292d60449da3cdff808c70173712869da7a0aa`.
- Open order `OPEN` at signed snapshot block **69901507**. The first history page shows the **same order identity and OPEN**, not a fill or cancel.
- Wallet snapshot **69901506**, position snapshot **69901507**. Both signed HTTP snapshots are non-atomic; **0 fills** and **0 positions** reported.
- UI says no **new aggregate** change between the *latest two reads*, which is consistent with the order staying open; earlier owner screenshot established the actual **0→1** count change.
- This is a **real normal order** for an operational workflow, *not* an incident, loss, execution, recovery, operator approval or differentiated market need.

The next read-only product increment compares subsequent signed order snapshots to the last observation. **If** the same `rq+oid` disappears and matching Perpl history carries `CANCELED`, the classification is `CANCELED_STATUS_OBSERVED` **not** recovered incident; absence of a matching terminal history event means `DISAPPEARED_OUTCOME_UNKNOWN`. The code never issues an order or a cancel, does not infer flat positions or no partial fills, and rejects cross-account comparisons or truncated live-open rows. Actual owner cancellation and outcome are not yet observed.

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
| Signed operator aggregate counts react to first real testnet order | **PROVEN by owner screenshots — 0→1 open orders** |
| Real order `rq/oid` details observed inside product | **PROVEN by owner screenshot, matching signed order and history rows** |
| Read-only cancel transition for this order | **IMPLEMENTED/LOCAL_TESTED; not yet owner-exercised** |
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
