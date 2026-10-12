# Perpl Incident Operations — conditional product brief

**Stage:** PRE-LOCK. Not authorized as a final hackathon concept.

**Target user:** operator managing automated trades through Perpl. Not necessarily the trader themselves.

**Verified negative event:** Desk's 2026-09-15 report of a trade filled at Perpl but displayed as expired by an out-of-date frame parser. Desk has since fixed its own issue.

**Root workflow hypothesis:** Incidents span client, websocket, exchange and account state. Operators need durable reconciliation and a safely actionable recovery step, potentially beyond any one client library.

**Current alternative:** Perpl's official `rq` idempotency, block/timing rules and snapshots; Desk OrderTracker; PerplBot. Code comparisons show significant existing coverage.

**Proposed core:** Detect and persist incident → obtain actual authenticated account status → classify UNKNOWN/CONFIRMED/CONFLICT → request scoped human authorization → perform permitted correction on testnet only → re-fetch position/order consequences → produce truthful audit receipt.

**Non-goals:** Autonomous trading strategies, live-mainnet deployment, raw key storage, unsupported execution claims, proof-only replay.

**Kill conditions:** No real recurring operator pain; same incident handled satisfactorily by a client/library; unavailable testnet API/credentials; cannot implement safe approved write and verify outcome; missing uniqueness within deadline.

**Metrics (not yet measured):** Time to truth, ambiguous-order rate, mistaken retries prevented, false escalation rate, operator intervention time, recovery completion rate, external adoption.

**Open questions:** Who operates it, how do they connect a read-scope Perpl account, what is a meaningful recovery action, and how does the workflow outrun configuring the existing client?

## Definition of Product Completion — non-bypass (2026-10-12)

This project applies the **already-promoted** [Product Reality Policy](https://github.com/Faadil1/faadil-agent-system/blob/main/PRODUCT-REALITY-POLICY.yaml); it does **not** create a new global gate. Source-of-truth project verdict: [PRODUCT_DEPTH_ACCEPTANCE.json](./PRODUCT_DEPTH_ACCEPTANCE.json), validated on every CI run.

**What is PROVEN:** the operator connects to actual signed Perpl Testnet account reads; a real BTC order was observed with its original `rq/oid`, then owner-canceled at Perpl; the resulting action with a distinct `rq` and matching `oid` was correctly reconciled by Metropolis. This proves a **bounded live account/order observation slice**, **not** the claimed incident recovery product.

**What remains material before PRODUCT_COMPLETE:**

- An **actual problematic order outcome**, actual operator need, and a noncommodity, source-verified reason why native Perpl/Desk/PerplBot is insufficient. An artificial failure fixture does not satisfy this.
- An **integrated live incident lifecycle**, from trusted detection to durable tracked case, operator understanding/authorization, safe justified corrective response (actual exchange write **only if explicitly authorized and safe on Testnet**), and verified changed exchange/position/business state. Otherwise the product is still *read-only observability*.
- Meaningful **success, negative, boundary, refusal, outage, disconnect, duplicate/race and recovery** routes on the *same shared core*, including correct UNKNOWN/ABSTAIN and no dangerous retry. Complete history/pagination, websocket gaps, account identity/permissions and retained evidence where material.
- A usable **operator journey**, secure key handling, genuinely persistent state, action/recovery, time to first meaningful value, clean-room reproducibility, externally usable self-service and an independent operator trial when applicable.
- The **post-first-slice Product Exploitation Loop**: repeatedly close the highest-value, coherently justified depth gap with real integrations/actions/consequences. No arbitrary number of features; no cosmetic scope inflation.
- Receipts, audits, judge stories, deterministic replay and demo are **products of the canonical live path**. Never create a separate proof-only product or let a polished demo become the technical architecture.

**Workstream ordering** while material gaps remain: `PRODUCT_EXPLOITATION` primary; proof/evidence, UI polish and submission packaging secondary support. A sprint may validate a capability with a receipt, but **it cannot end there** if the material product workflow remains incomplete.

**Complete verdict:** only when the entire justified material product scope is functional, live, safely authorized where applicable, consequences verified, adverse paths covered, and all applicable canonical gates reconciled. The deadline, a working vertical slice, passing tests, one normal cancellation, videos and submission are not completion conditions. If time, access, safety or marginal value validly stops work, report **NOT_COMPLETE**, never manufacture a “ready” verdict.

**Current status:** NOT_COMPLETE / LIVE_CORE_LOOP BLOCKED / DIFFERENTIATOR BLOCKED / CONCEPT_LOCK BLOCKED. Product state is the source of truth; proof count never upgrades it.
