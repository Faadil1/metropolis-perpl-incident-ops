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
