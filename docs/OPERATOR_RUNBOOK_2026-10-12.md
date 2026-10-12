# Metropolis Perpl Incident Operations — operator runbook

**Version:** 2026-10-12 · **Mode:** Local, Monad Testnet, READ API only.
**Readiness:** BUILT / LOCAL_VERIFIED for the operator case workflow; **NOT COMPLETE** for a real externally validated incident-recovery product.

## One running product, not a demo harness

The operator UI, signed HTTP refresh, optional local polling, persisted operator case register and case ledger all use the same `IncidentStore` SQLite connection. The manual test frame lab is folded away and marked `MANUAL_UNVERIFIED`. Cases cannot be created by posting a fixture to the live case API.

**Real runtime loop:**

1. A real signed GET reads Testnet WalletSnapshot, OrdersSnapshot, PositionsSnapshot and first-page OrderHistory/Fills.
2. The account overview validates network and account; the order observer sanitizes actual `rq/acc/mkt/oid/st/sr/fr`, with explicit history-page caveat.
3. The lifecycle comparator checks earlier signed observations for positive matched states; absence is `UNKNOWN`, not `FAILED`.
4. Only a positive venue-history failure (`st=7`) or an evidence-backed uncertain order transition can create a durable operator case. Normal OPEN and normal CANCELED never auto-create an incident.
5. Case identity is account + market + original rq + optional oid + kind. Repeated refreshes update the existing case, without duplicating the case-created event.
6. A localhost operator can **ACKNOWLEDGE**, **HOLD**, **ESCALATE**, **REQUEST_RECHECK**, or **CLOSE_REVIEW** with an actor name, justification, optimistic version and idempotency key. Each write changes durable local state and appends a hash-linked event. **No action posts an order, changes leverage, cancels or withdraws on Perpl.**
7. After an unresolved order has later positive terminal history with the same account+market+order ID and original request correlation, the existing case moves to **RECONCILED_REVIEW_NEEDED** with a positive venue verdict. Closing the review is possible only after that evidence; it **does not mean the incident or account was recovered**.
8. Monitoring is operator-controlled: optional signed polling at 45 seconds, same live refresh path. It stops with the localhost server and has **no production uptime SLA**.

## Running on Windows

```powershell
cd "$HOME\metropolis-perpl-incident-ops"
git switch research/live-depth-foundation
git pull --ff-only
.\.venv\Scripts\python.exe -m pytest -q
.\scripts\start_operator_readonly.ps1
```

Enter only a separate **READ** API token and the matching Ed25519 signing secret at the masked PowerShell prompts. They stay in local process memory, not in the repo, GitHub Issues or screenshots.

Open **http://127.0.0.1:8765**. Use **Actualiser le compte Testnet LIVE** for an authenticated read, then inspect **Dossiers opérationnels**. If appropriate, turn on **Activer le suivi signé (45 s)**. The new cases appear only if the exchange actually supplies positive failure/uncertainty evidence. No result on a normal account is correct and does not imply all possible incidents are absent.

For a case: open the case, inspect the evidence, write a specific reason, choose a local action and save. If needed press **Relire Perpl**; compare the venue result. The local ledger says `LOCAL_TAMPER_EVIDENT_NOT_IMMUTABLE`, not on-chain permanence.

## Exact limits / fail-closed boundaries

- **READ-only exchange:** no `TRADE` key is requested, stored or used. Application never sends any exchange order/cancel and cannot block transactions created by other Perpl apps.
- **HOLD is an operator signal**, not a venue guardrail. Clients trading externally must be stopped or restricted by their own controllers.
- **Actual remediation is not implemented or verified.** Owner's historical user-executed normal cancellation is real but **not** an incident resolved by this application.
- The history reader now attempts **up to 5 signed GET pages** for order history and fills (configurable cap 1–10); only fully exhausted `np` may set `scan_complete=true` for that bounded read. An incomplete scan or time gaps are **not** proof that an order never executed. Live pagination remains pending owner-side verification.
- Wallet, open orders, positions and history are separate **non-atomic HTTP snapshots**. Zero current positions does not prove no earlier partial fill.
- Polling is **best effort**, no formal latency/error budget and no verified WebSocket-to-case convergence under stream gaps. Persisted local data is not independently tamper-proof.
- CSRF/Origin checks and the ephemeral operator session support a **localhost owner-only context**. This is not remote multi-user authentication, RBAC, production encryption or secure public hosting.
- External operator demand, material advantage versus Perpl native/Desk/PerplBot, independently observed genuine failure/recovery and release authorization remain **BLOCKED**.
- A user-provided account screen/video is user-observed runtime evidence, not independent auditor validation.
- An outage or a skipped poll is a monitoring failure; **do not** infer an exchange order was rejected. The monitor records failed-read counters without generating fake exchange cases.

## Product-evolution next gates (not optional for PRODUCT_COMPLETE)

1. Real operator incident from a genuine venue failure or externally verifiable ambiguous result, and an independently supported counterfactual versus existing clients.
2. Whole-history pagination with bounded signed cursor checks, position/fill consequence reconciliation, lost-status and gap repair.
3. Explicitly authorized, safe *testnet-only* value-changing corrective action (if core value requires it), permissions, idempotency, no-duplicate invariant and verified venue after-state.
4. Independent operator self-serve trial, security/clean-room validation, reliability evaluations, measured time-to-first-value and economics.
5. Exact hackathon eligibility/judge obligations and terminal assurance. If deadline intervenes, truthfully mark **NOT_COMPLETE**, not a demo-as-product.

**Project gate registry:** [GATE_REGISTRY_PRELOCK.yaml](../GATE_REGISTRY_PRELOCK.yaml); **project completion:** [PRODUCT_DEPTH_ACCEPTANCE.json](../product/PRODUCT_DEPTH_ACCEPTANCE.json). The central [Product Reality Policy](https://github.com/Faadil1/faadil-agent-system/blob/main/PRODUCT-REALITY-POLICY.yaml) takes precedence.

## 2026-10-12 screen review and bounded signed pagination

A new owner-uploaded 26.20-second video independently of our local CI shows the actual owner localhost UI rendering account 1060, 0 open orders, 0 positions, 2 first-page history events, 0 first-page fills, `CANCELED_STATUS_OBSERVED` and exactly 0 operational cases. The monitor remains stopped. See [sanitized owner evidence](../evidence/sanitized/PERPL_OWNER_LOCAL_OPERATOR_SCREEN_2026-10-12.md). No genuine failed trade or operator case decision was shown.

**Updated history depth (code now locally verified by mocked transport):** Perpl `np` cursors trigger additional signed GETs for order-history/fills, bounded to 5 pages by default and 10 max. A second-page failure can reach the actual persistent operator case workflow. `history_scan.complete=false` means the scan was incomplete; do not deduce that unobserved orders did not execute. Page errors, invalid cursors and loops fail the signed read rather than silently recording partial truth. The first-page panels remain an explicit first-page view; the pagination status now reports pages/events scanned separately.

**Not yet done:** owner-run signed Testnet pagination retest, unbounded/exhaustive history where >5 pages exist, verified account-position consequences, and actual incident remediation.
