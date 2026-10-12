# Negative-event and competitive-novelty reality check — 2026-10-11

**Status:** PRE-LOCK RESEARCH. This is a qualification decision, not a concept selection. No synthetic trade is valid LIVE evidence.

## 1. What has actually been proven

- Owner-authenticated Perpl Testnet GET and local operator UI, account 1060, chain 10143.
- Genuine BTC Testnet order: OPEN in signed exchange snapshot, original `rq` + `oid` correlated to history.
- Genuine owner cancellation from the venue with a **new action `rq`** referencing the same **order `oid`**. Patched operator classified `CANCELED_STATUS_OBSERVED` in a second owner video.
- This is a **normal exchange operation**, not an operational incident or a product-performed recovery.
- A real *bug in our operator* was exposed by actual venue data: strict equality of cancel-action and original `rq` had incorrectly hidden the terminal transition. We corrected and user retested it; this is a valuable engineering regression, not proof of market novelty.
- **No observed failed Perpl trading request**, failed fill, multi-client race, actual duplicate order, negative safety consequence or third-party trial yet.

## 2. Existing solutions and native reality

| Solution | Source-confirmed abilities | Our collision / gap |
| --- | --- | --- |
| Perpl native API | Authenticated order/position snapshots, order/fill histories, `rq` idempotency, reason codes, WS seq-gap and documented safe retries | Basic status + data availability + retry correctness are **already native**. A client can implement basic recovery. |
| Desk | Live trading app; `OrderTracker` tracks `rq`, batched `mt:24`, definitive vs late failure, timeout, fills; real postmortem and fix | Single-client correctness is **solved by competitor** for that incident. Never claim Desk still falsely marks fills as expired. |
| PerplBot | Trading SDK/CLI/chatbot, position management and cancellation, transaction forensics, dry-run/fork | Basic trading execution, cancel buttons, receipts and simulation are not novel. |
| Proofbook | Agent vault policies, live integrations, execution receipts and freeze/monitoring ambitions | Trust limits and proof surfaces already explored. Do not claim exclusive reliable-trade governance. |

Primary public sources:
- [Perpl official API docs](https://github.com/PerplFoundation/api-docs/blob/main/README.md)
- [Perpl websocket retry/sequence guidance](https://github.com/PerplFoundation/api-docs/blob/main/websocket.md)
- [Perpl type/status and failure reason registry](https://github.com/PerplFoundation/api-docs/blob/main/types.md)
- [Desk `OrderTracker.swift`](https://github.com/frankolien/desk/blob/main/DeskKit/Sources/DeskPerpl/OrderTracker.swift)
- [Desk historical audit](https://github.com/frankolien/desk/blob/main/docs/perpl-order-400-audit-2026-09-15.md)
- [PerplBot](https://github.com/0x70626a/PerplBot)
- [Proofbook](https://github.com/ProofBook-App/proofbook)

## 3. Demand signals (NOT Perpl-specific adoption)

A public January 2026 [r/algotrading discussion](https://www.reddit.com/r/algotrading/comments/1qjazo0/how_do_you_all_deal_with_exchange_api_failures/) explicitly mentions API timeouts with uncertain order placement, double fills and disagreements between private and public endpoints. A September 2026 [r/algotradingcrypto discussion](https://www.reddit.com/r/algotradingcrypto/comments/1wgrxpk/tradingview_webhook_exchange_execution_how_do_you/) asks about preventing duplicate orders and reconciling executions with the exchange, including separate monitoring.

These are self-selected community anecdotes from **other exchanges**. They justify a discovery hypothesis; they do **not** establish a buyer, Perpl customer pain, differentiated value or willingness to pay.

## 4. Narrow hypothesis worth testing (NOT LOCKED)

**Independent operator truth-and-hold desk for automated Perpl clients**, especially when an application loses a status response or another client initiates a conflicting action:

1. Detect a **positive** exchange failure event (`st=7`, `sr`, optional `fr`) or independently observed ambiguity after an open order disappears with no matching terminal history. Avoid deriving incidents from `fw=false`, empty accounts, missing first-page histories or unauthenticated reports.
2. Reconcile `account + market + oid` across client command actions, preserving distinct `rq` values. For failed pre-order submissions with no on-chain `oid`, track by `account + market + rq` without inventing an order id.
3. Preserve cause, provenance and UNKNOWN. Do not send another order when result is uncertain. Perpl's `sr=32` has an official narrowly bounded retry exception, **not** blanket permission for an unsupervised duplicate.
4. Show the operator **what must be checked next** and exactly why no action is yet safe.
5. A future authorized corrective operation must be **testnet only**, owner-permission-bound, consequence-verified and measured against what the existing Perpl client can already do. Today **not implemented**.

**Current product increment:** `negative_review.py` computes read-only review cases from **successfully signed Perpl first-page history or previous signed observation comparisons**. It handles historical rejection before any real `oid` exists. UI deliberately shows no cases on an empty account, even if order forwarding is intentionally OFF. API keys remain local, and no exchange write is possible. Only automated fixtures exercise rejection cases so far.

## 5. Kill / go/no-go tests

**Differentiation gate = BLOCKED** until each of these passes with source evidence:

1. **Specific user:** at least one independent operator of automated Perpl trades describes an actual incident, their existing workaround and measurable impact. If no accessible operator / need, **KILL or PIVOT**.
2. **Competitive counterfactual:** reproduce operator decision with Perpl official UI + Desk + PerplBot (where applicable). The new workflow must demonstrate a *material*, not cosmetic, advantage over their existing failure handling.
3. **Negative-event truth:** observe at least one **authentic Perpl Testnet failure/ambiguity** in signed exchange data or an externally provided verifiable trail. Reconstructed local fixtures do not prove that such a failure occurred during testing.
4. **Useful action:** show the operator can choose a safe response and verify its real consequence, instead of just reading an error code. Without a load-bearing action or confirmed decision consequence, the build is **OBSERVABILITY_ONLY**.
5. **Reliability/economics:** multiple source-specific negative/recovery runs; test outage, lost status, partial history, false join, key revocation, wrong-account and repeated-refresh scenarios. No claim that one green run proves reliability.
6. **Deadline:** official Metropolis submission deadline is **October 13**; exact time and requirements must be checked in the authenticated portal before a Concept Lock or submission promise.

## 6. Gate decision

- PAIN / DEMAND: **ACTIVE / UNKNOWN for Perpl owners**, community evidence general.
- NEGATIVE_EVENT: **PROVEN historical Desk postmortem**; **ACTIVE** for live Perpl owner failure.
- DIFFERENTIATOR: **BLOCKED**.
- TECHNICAL_REALITY: **PARTIAL PROVEN** for signed reads and normal cancel; **ACTIVE** for rejected request handler and external negative trials.
- NEGATIVE_PATH: **ACTIVE (LOCAL TESTED for failures; live verified only for normal cancellation)**.
- EVIDENCE_INTEGRITY: **ACTIVE**.
- EXECUTION, LIVE_CORE_LOOP, JUDGE_SELF_SERVE, CONCEPT_LOCK: **BLOCKED**.
- Production / mainnet trading: **FORBIDDEN / BLOCKED**.

No invented stage or replacement of the canonical 62-gate registry.
