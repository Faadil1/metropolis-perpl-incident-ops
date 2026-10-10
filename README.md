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
