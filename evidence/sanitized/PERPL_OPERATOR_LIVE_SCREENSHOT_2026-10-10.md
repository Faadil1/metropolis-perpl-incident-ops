# Owner-observed LIVE account read inside operator UI — 2026-10-10

**Provenance:** USER-SUPPLIED SCREENSHOT, viewed in current conversation. The screenshot is not attached to the public repo. No wallet address, key, secret, raw response body or sensitive balance is published.

**Local UI:** `http://127.0.0.1:8765`.

**Observed status label:** `SIGNED PERPL GET / TESTNET / LIVE ACCOUNT SNAPSHOTS`.

**Partial visible payload:**
- Snapshot blocks — wallet: **69883405**, orders: **69883406**, positions: **69883407**.
- First-page order-history count **0**, fills count **0**, and `has_more_pages=false` for both.
- `non_atomic_http_reads=true`.
- `exchange_writes_enabled=false`; `incident_recovery_proven=false`; `live_core_loop_proven=false`.
- Full top section of scrollable JSON was not visible; do **not** extrapolate accounts, balances or other hidden fields from the screenshot.
- Previous owner-run independent signed GET check reported five endpoints HTTP 200 and zero open orders and positions (see [separate sanitized proof](./PERPL_SIGNED_READ_2026-10-10.md)).

**Verdict:** Real Perpl Testnet authenticated account-read route **PROVEN in local operator application by owner screenshot**. This is not evidence of trading, a recovered incident, adoption by a third-party, a secured public deployment, or Concept Lock.

**Next action:** Observe a second real state of the same account and classify changes as review-only, with no automatic incident or exchange write.
