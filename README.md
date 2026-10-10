# Perpl Incident Operations — Metropolis 2026

**Status:** PRE-LOCK research build · **LOCAL_VERIFIED** only · **NOT LIVE** · **NO trading/exchange writes**

A prospective operator-facing incident recovery product for Perpl on Monad. The source of truth is this repository; the historic [Valid Until](https://github.com/Faadil1/valid-until-agent-os) repository remains frozen and separate.

## Problem

An API order can be accepted or filled even when a trading client's response is lost or misclassified. Perpl distinguishes acknowledgements from fills and specifies strict `rq` idempotency and websocket sequence rules. A real incident was published by [Desk's September 2026 audit](https://github.com/frankolien/desk/blob/main/docs/perpl-order-400-audit-2026-09-15.md): a filled order was displayed as expired, and Desk corrected the implementation. This is evidence of a historical failure **already repaired by that competitor**; it is **not proof of unmet demand**.

## Current gates

- Concept Lock: **BLOCKED**
- Differentiation versus Desk/PerplBot/native Perpl: **BLOCKED**
- Authenticated Perpl testnet account connection: **NOT PROVEN**
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

See the research PR for the code baseline, tests, CI and the full conditional-gateway registry. Sources: [Perpl API docs](https://github.com/PerplFoundation/api-docs), [MetaMask Agent Wallet](https://github.com/MetaMask/agent-wallet-plugin-examples).

Deadline published by Monad: **2026-10-13**; verify the exact submission time on the authenticated portal.
