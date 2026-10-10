# Perpl Testnet — Signed Read Evidence (2026-10-10)

**Classification:** USER_REPORTED_SANITIZED_LOCAL_EXECUTION · AUTHENTICATED_READ_PROVEN

The owner ran the research-branch client on a dedicated Windows environment and reported the following safe aggregate results:

| Observation | User-provided value |
| --- | --- |
| GitHub branch | `research/live-depth-foundation` |
| Local test suite | 34 passed in 1.07 seconds |
| Network | Monad Testnet, chain ID 10143 |
| Classification | `PERPL_TESTNET_AUTHENTICATED_READ` |
| Wallet signed GET | 200 |
| Orders signed GET | 200, 0 items |
| Positions signed GET | 200, 0 items |
| Order history signed GET | 200, 0 first-page items, no next page |
| Fills signed GET | 200, 0 first-page items, no next page |
| Exchange writes enabled | false |
| Authenticated core loop proven | false |

The credential values, wallet address, exchange account IDs, balances and original unredacted response bodies are **not** present. This source is the owner's sanitized terminal output supplied during the current chat, not an independently retained live HTTP trace.

**Verdict:** Signed Perpl Testnet account reads observed. No live order, failure, incident, remediation, trading write, downstream consequence, payment or demand established. Do not promote product Live Depth based on this step alone.

**Next relevant evidence:** real account overview from the operator app, then observed trading state and an authorized resolution with true execution-status reconciliation. 
