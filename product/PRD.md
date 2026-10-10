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
