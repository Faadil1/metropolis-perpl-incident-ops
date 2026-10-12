# Owner-observed cancellation — true exchange history, discovered comparator bug

**Observed:** 2026-10-11 local / 2026-10-12 UTC, owner-provided MP4 (~22.4 sec) of the actual local Metropolis operator surface. The recording and sensitive account payloads are not shared to public GitHub.

- Testnet account **1060**, BTC market **16**, **0 open orders**, **0 open positions**.
- Perpl signed order-history first page contains **two events** for the same `oid`: the original **OPEN** and later **CANCELED**.
- The terminal CANCELED event has a **different** `rq` from the original OPEN event, as expected from a separate cancel command.
- First-page fills **0**. This does not prove an absolute absence of partial fills in all history.
- Original order tuple SHA-256: `b90a6004e8389540821a673d89292d60449da3cdff808c70173712869da7a0aa`.
- New cancel command tuple SHA-256: `e5eee005655ba395e4ee1fedd735a38594ec96dd50b58281eca32c00674b7e82`.
- The actual owner UI displayed **"Aucune évolution d'ordre prouvée entre ces deux observations."** despite this positive historical cancellation evidence.

**Bug source:** code required identical creation and cancellation `rq` to join, while Perpl's cancellation uses a fresh `rq` and references the order by `oid`. Repeated refreshes already overwrote the prior signed OPEN as the immediately previous observation, so even a correct join across latest-only snapshots would miss it.

**Resolution implemented, awaiting live owner retest:** order key = (account,market,oid), preserve the original and cancellation `rq`, require a positive matching terminal historical status, scan up to 512 SHA-validated historical sanitized account observations. No manufactured events or exchange writes. Cross-account and conflicting statuses remain fail-closed. Regression tests mimic the observed semantics.

**Status:** owner video proves normal exchange cancellation, *not* a resolved business incident, all-fill absence, proven production monitoring, live fixed UI, market demand, or concept lock.
