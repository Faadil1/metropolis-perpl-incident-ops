# Security and safe use

This is an **unaudited research build** for Monad Metropolis 2026. **DO NOT use with real funds**, do not expose the local server to an untrusted network, and do not consider any displayed status final until reconciled with the exchange.

- API key material must remain in local environment variables, never in Git, logs, screenshots, browser forms, issues or PRs.
- Only **read-only testnet** credentials are supported by the application. Write/trading credentials and mainnet execution are out of scope.
- Do not infer failed execution from a timeout, missing WebSocket frame, reconnect or local UI expiration.
- No automatically generated cancellation/trade request is permitted until authorized exchange writes, idempotency and consequence verification are implemented and reviewed.
- The hash-linked SQLite ledger is **local integrity checking**, not an immutable blockchain proof; an actor who controls the DB can rewrite it.
- External network/API failure must resolve to UNKNOWN, with read-only reconciliation and explicit operator recovery.
- No claimed LIVE evidence without actual exchange read or transaction receipt and provenance.

Report sensitive findings privately to the repository owner, and avoid posting secrets or unredacted account data.

## Local operator workflow and security boundary (2026-10-12)

- The FastAPI server is explicitly **localhost-only**. A middleware checks allowed Host and Origin on all requests; operator decisions and monitor controls additionally need a session token generated only in server memory and retrieved same-origin. This is **not** production multi-user authentication, RBAC, or protection against malware already running on the same machine.
- Owner decisions are local SQLite writes; their `actor`, `reason`, optimistic version and idempotency key are retained. The app never stores Perpl signing keys in case rows and has no trade-scope API.
- A `HOLD` is only a local operational signal. It **does not stop any other Perpl client or user** and cannot prevent fills of resting orders.
- Background polling is optional, best effort, only uses READ signed Perpl GET and stops with the process. Failed signed reads count as monitor failures, never as proof of venue rejection.
- Signed HTTP snapshots remain **non-atomic** and order/fill history is first-page-only. Operator closure is not exchange recovery; exposure/positions must be re-verified through the source.
