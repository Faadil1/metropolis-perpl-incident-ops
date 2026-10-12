# Product Depth & Live Reality — pre-lock

## Material product capability increment — 2026-10-12

**Built on the shared live account service:** signed account observation automatically creates a uniquely identified, persistent operator case for genuine failed history or a signed-derived UNKNOWN transition. A local operator changes persistent case state with explicitly justified ACK/HOLD/ESCALATE/REQUEST_RECHECK/CLOSE_REVIEW; signed rechecks can mark an actual later positive terminal exchange outcome. The optional owner-controlled monitor polls the same actual Perpl signed READ pipeline. The audit is a local hash chain, not immutable evidence.

**Scope of proof:** new workflow is `LOCAL_VERIFIED` with isolated signed-read fixtures and CI; it has **not** been exercised on an actual failed order in the owner account. The prior genuine normal Testnet order and cancel remain separate `OWNER_LIVE_OBSERVED` facts. No transaction from Metropolis, exchange-wide block, autonomous trade retry, reliable cross-client guardrail, externally operated incident recovery or market novelty is proven.

**Highest safe action tier achieved:** logged local workflow writes (operator decisions), NOT exchange write or market consequence. Next material action still requires explicit owner authority and a real, safe Testnet use case. The 18 material product-depth gaps remain open; no terminal promotion. Full [runbook and failure boundaries](../docs/OPERATOR_RUNBOOK_2026-10-12.md).


## Non-compromise priority enforcement — 2026-10-12

**Primary workstream: PRODUCT_EXPLOITATION.** The real signed Perpl Testnet observation and normal cancel constitute a bounded live *observation* slice. They do not discharge the product's material commitments: a real incident, independently relevant operator pain, a safe authorized and meaningful operator action, verified after-state and operational resilience. Source contract: [PRODUCT_DEPTH_ACCEPTANCE.json](../product/PRODUCT_DEPTH_ACCEPTANCE.json).

At each material work touch: inventory remaining causal product depth, select the highest-value justified delta, build into the shared live runtime, test representative success/negative/boundary/failure/recovery, and emit evidence from actual execution. Continue while justified value/differentiation outweighs cost, risk and deadline. Never stop because enough tests, screenshots, a replay or a demo exist.

**Status of project:** `NOT_COMPLETE`. The first normal order cycle is `PROVEN`; the *incident core* is `BLOCKED`. The post-slice exploitation review is `ACTIVE`. Deadline or safety constraints may stop work but must not change the truthful readiness claim. This is enforcement of existing central canon, not a new stage or gate.


**Status as of 2026-10-10: owner-observed LIVE authenticated reads in the local operator UI; LIVE CORE LOOP = BLOCKED.**

## Negative-path operator evaluation — pre-lock research 2026-10-11

Direct Perpl source analysis and code competitor checks show that **status tracking, idempotency, cancellation, existing history and basic recovery are native or already implemented by Desk/PerplBot**. A new read-only review surface is not alone evidence of product differentiation.

The new candidate capability reads signed order-history refusal entries (`st=7`) and their `sr/fr` cause, and can classify disappearance without positive terminal history as `UNKNOWN_NOT_FAILED`. Genuine pre-order refusals can lack an assigned `oid`; this must no longer cause the whole owner account refresh to return 503. A wallet with `fw=false` and **no failed request** is *not* an incident.

This feature is **LOCAL TESTED ONLY**, not owner-tested on an actual failed order. It does not initiate a new order, retry, enable forwarding, cancel, sign or grant trade permissions. No evidence yet shows an external Perpl operator using or valuing this workflow. Detailed [competitive reality and kill conditions](../research/NEGATIVE_EVENT_NOVELTY_REVIEW_2026-10-11.md).

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

## Owner LIVE regression retest — cancellation join fix PROVEN (2026-10-11 EDT / 2026-10-12 UTC)

Owner supplied a **new 37.2-second MP4**, captured after updating the local operator application to the repaired code. The recording is retained only in this conversation, **not uploaded to public GitHub**. Video SHA-256 commitment: `de35d38f2544bf41bd5ddd690351bd183eb47530b51ba9ac4cb8985f1c35ca78`.

Visible in the actual local Metropolis UI after Perpl signed GET:
- **CANCELED_STATUS_OBSERVED** in **Évolution vérifiée des ordres**.
- Matching original order identity for **account 1060 / BTC market 16**.
- Explicit **HISTORIQUE CORRÉLÉ** with **separate cancellation action rq**, whereas the `oid` is shared with the original OPEN order. Exact IDs are in the private recording; do not reproduce them publicly.
- **0 open orders**, **0 positions**, **2 first-page history events**, **0 first-page fills**.
- Newer sample signed wallet/open-order/position blocks **70283822 / 70283823 / 70283824**, explicitly **non-atomic**.
- Explicit UI flags **POSITION NON VÉRIFIÉE** and **PAS UNE RÉCUPÉRATION**; **zero exchange writes from the application**.

**Verdict:** Bug fix (new terminal action rq, same oid, history retained across reads) is **PROVEN on the owner's actual authenticated local Testnet path**. This was a normal user-issued cancellation through Perpl, *not* an incident handled by Metropolis. The app does not prove all historic fills, the position consequence at a perfectly simultaneous block, competitor differentiation or a production service.

**Next milestone:** identify a genuine negative event / ambiguity, then verify a real safe operator response and measurable product differentiation before Concept Lock. Do not create new live orders solely for a showcase or silently enable a TRADE key.

## Live cancellation evidence and discovered bug — owner video, 2026-10-11 local / 2026-10-12 UTC

**New genuine external evidence:** Owner-provided 22.4-second MP4 recording of the local operator UI after canceling the real Testnet order. The video is not published or saved in public GitHub.

Signed Perpl account summary in the operator UI: **account #1060**, **0 open orders**, **0 open positions**, **2 first-page historical order events**, **0 first-page fills**. History row #1 carries **CANCELED**, history row #2 carries **OPEN**. Both use the same original `oid`, account and market **16**. The `rq` for the `CANCELED` row is *different* from the `rq` for the original `OPEN` row. The original order identity commitment is `b90a6004e8389540821a673d89292d60449da3cdff808c70173712869da7a0aa`; terminal cancel command identity commitment is `e5eee005655ba395e4ee1fedd735a38594ec96dd50b58281eca32c00674b7e82` (SHA256 of `10143|acc|mkt|rq|oid`; no exact IDs publicly republished).

**Product bug observed on live owner path:** UI incorrectly said `Aucune évolution d'ordre prouvée entre ces deux observations.` The code joined terminal history by **original `rq` + `oid`** and compared only the latest two snapshots. The real Perpl cancellation uses a **new request ID** referencing the **same order ID**. [Perpl's official websocket example](https://github.com/PerplFoundation/api-docs/blob/main/websocket.md#placing-orders) shows cancel order as a new command with `rq: Date.now()` and `oid: orderIdToCancel`, consistent with the observed evidence.

**Repair:** The read-only lifecycle comparator now identifies the *order* with (account,market,oid), records both the original request ID and the terminal action request ID, checks positive terminal history, fails closed for missing/conflicting history and never treats a normal cancel as incident recovery. It searches earlier SHA-verified locally persisted signed account snapshots (up to 512) to recover the earlier OPEN after intermediate 0-open refreshes or a process restart. This is a bounded experimental capability, not production wallet isolation, complete history pagination or reliable long-term replay. Tests include the real observed distinct-`rq` case.

**Truth boundary:** **Perpl historical cancellation = OWNER-VIDEO OBSERVED**, **Metropolis status correction = PROVEN BY SUBSEQUENT OWNER VIDEO**. Zero first-page fills and zero open positions do not prove that no prior partial execution ever happened. No real incident recovery, external adoption, defensible novelty or Concept Lock claim.

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
| Perpl signed historical `CANCELED` for prior real order | **PROVEN by owner-provided video**, different action `rq`, same `oid` |
| Fixed comparator showing `CANCELED_STATUS_OBSERVED` on owner device | **PROVEN in second uploaded screen recording** |
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
