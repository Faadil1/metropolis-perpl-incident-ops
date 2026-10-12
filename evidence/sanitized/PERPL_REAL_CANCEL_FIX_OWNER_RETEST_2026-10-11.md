# Perpl real cancel reconciliation fix — owner LIVE retest PROVEN

- **Observation date:** 2026-10-11 local, video recorded UTC 2026-10-12.
- **Evidence class:** owner-uploaded 37.2-second screen recording from the genuine local `http://127.0.0.1:8765` operator UI, connected via authenticated Perpl Testnet GET; **not** a code-generated fixture, preseeded output, simulated exchange or independently fetched API trace.
- **Recording SHA-256:** `de35d38f2544bf41bd5ddd690351bd183eb47530b51ba9ac4cb8985f1c35ca78`. Video is not published in GitHub.
- **Account:** 1060; **network:** Monad Testnet 10143; **market:** BTC / 16.
- **Observed terminal status in product:** `CANCELED_STATUS_OBSERVED`.
- **Observed correlation:** `HISTORIQUE CORRÉLÉ`, the original `oid` is retained, cancellation has a *different* `rq` from the original request. Original and action request identifiers are visible only in the private user recording.
- **Current signed aggregates:** 0 open orders, 0 open positions, 2 first-page historical events, 0 first-page fills.
- **Example block readings in video:** wallet `70283822`; open orders `70283823`; positions `70283824`. Three HTTP reads are **non-atomic**.
- **Safety / truth UI:** explicitly states **POSITION NON VÉRIFIÉE**, **PAS UNE RÉCUPÉRATION**; no exchange write from Metropolis.

### Verdict

**PROVEN from owner-operated LIVE Testnet UI:** the prior real failure to correlate a cancellation with a new `rq` was fixed. The app matched original order and cancel action using `account+market+oid`, retaining separate request identities, and retrieved prior signed observation history as needed.

**Not proven:** any exchange cancel or trade executed by Metropolis, prevention/recovery of a real business incident, full historical fills and synchronized position consequences, third-party demand, competitive differentiation, end-to-end production readiness or Concept Lock.

Corresponding code at [bd7bf25](https://github.com/Faadil1/metropolis-perpl-incident-ops/commit/bd7bf25022476a4ea1e968aa4d95b5db3844d2c5), validated by CI **74 tests passed** before this evidence-only update.
