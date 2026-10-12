# Perpl Incident Operations — Metropolis 2026

**Status:** PRE-LOCK research build · **LIVE AUTHENTICATED TESTNET READS PROVEN BY OWNER** · **LIVE CORE LOOP BLOCKED** · **NO trading/exchange writes**

A prospective operator-facing incident recovery product for Perpl on Monad. The source of truth is this repository; the historic [Valid Until](https://github.com/Faadil1/valid-until-agent-os) repository remains frozen and separate.

## Problem

An API order can be accepted or filled even when a trading client's response is lost or misclassified. Perpl distinguishes acknowledgements from fills and specifies strict `rq` idempotency and websocket sequence rules. A real incident was published by [Desk's September 2026 audit](https://github.com/frankolien/desk/blob/main/docs/perpl-order-400-audit-2026-09-15.md): a filled order was displayed as expired, and Desk corrected the implementation. This is evidence of a historical failure **already repaired by that competitor**; it is **not proof of unmet demand**.

## Current gates

- Concept Lock: **BLOCKED**
- Differentiation versus Desk/PerplBot/native Perpl: **BLOCKED**
- Authenticated Perpl testnet account connection: **PROVEN by sanitized owner terminal output (five HTTP 200 reads)**
- Authenticated account overview in local operator UI: **PROVEN by owner screenshots**; snapshot blocks 69,883,405–69,883,407 and subsequent 69,893,555–69,893,557; HTTP reads non-atomic
- Authenticated account comparison **PROVEN with no aggregate change**; one account (#1060), 0 orders/positions; no incident inferred
- Read-only genuine order observer: **IMPLEMENTED, NOT YET LIVE-EXERCISED**; observed order IDs originate only from signed Perpl order snapshots/history, no synthetic trading
- Live incidents, authenticated cancellation, actual downstream trade consequences: **NOT IMPLEMENTED / NOT PROVEN**
- Historical real negative event: **PROVEN as a documented source**, independent external demand unknown
- No production-readiness or security assurance claim

The project must earn its differentiation as *operator incident recovery with durable state, explicit authorization and confirmed consequences*, not a generic order tracker or proof-only demonstration.

## Operating principles

- Live core value and real consequences outrank replay and demo assets.
- A network timeout is **UNKNOWN**, never a failed order.
- Request ID (`rq`) is the idempotency key; never submit an unverified duplicate with a new ID.
- Exchange state and authenticated position/order reads outrank locally entered frames.
- **No secrets** in Git history, issues, screenshots, fixtures or browser forms.
- If actual Perpl access is unavailable, explain the blocked gate; never relabel fixtures as live.
- No mainnet trading or real-money flows are authorized.

## Observe your real testnet account safely

For the owner-controlled Windows setup (no credentials in chat or GitHub), see [the read-only guide](./docs/PERPL_TESTNET_READONLY_SETUP.md). Start the local operator with `scripts/start_operator_readonly.ps1` and click **Actualiser le compte Testnet LIVE**.

The account overview is a useful starting point for real operator work. Two successive signed reads may indicate changes in aggregate open-order/position counts or account flags; **none of those changes alone proves an incident, failure, fill, or completed recovery**. New account scopes are not silently compared, and a regressed snapshot block requires investigation.

Current negative-path and competitor novelty gates remain active. A true business outcome still requires a real request/order, authenticated reconciliation, human authorization for any safe corrective action, and verified post-action state.

See the research PR for the code baseline, tests, CI and the full conditional-gateway registry. Sources: [Perpl API docs](https://github.com/PerplFoundation/api-docs), [MetaMask Agent Wallet](https://github.com/MetaMask/agent-wallet-plugin-examples).

Deadline published by Monad: **2026-10-13**; verify the exact submission time on the authenticated portal.

## Genuine Testnet order milestone (owner evidence, October 10)

A user-entered BTC Testnet limit order was independently observed through Perpl's
signed account API in the local operator UI. The matching open-order/history
identity is **proven by owner screenshot**, with commitment digest
`b90a6004e8389540821a673d89292d60449da3cdff808c70173712869da7a0aa`.
The actual order identifiers are intentionally not published here.

The account read and order correlation are real, but the order is a *normal*
exchange event, not an incident. A read-only lifecycle comparison can classify
a future matching `CANCELED` history event, but **actual owner-side cancellation
has not yet been observed** and neither canceled status nor a missing order
automatically proves absence of fills or positions.

## Normal Perpl Testnet cancellation — live behavioral finding

An owner video recorded on October 11 local time (October 12 UTC) proves a
historical **CANCELED** status from a real Perpl order previously OPEN.
It has **the same order ID (`oid`) but a different cancel-action request ID
(`rq`)**. This exposed a real bug in our old status join. The read-only
comparator now matches the order by account/market/oid and preserves both
request IDs. It uses bounded, digest-verified persisted observations to bridge
repeated refreshes and restarts. Retest in the owner local runtime is pending.

This is a **normal owner-originated cancel on Perpl**, not an incident recovery.
No exchange writes have been implemented in Metropolis, and there is no
evidence of actual order fills in the first history page or an open position.
