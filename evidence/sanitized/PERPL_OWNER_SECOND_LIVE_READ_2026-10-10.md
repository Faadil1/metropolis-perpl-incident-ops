# Second authenticated Perpl account observation — owner UI, 2026-10-10

**Evidence:** Screenshot supplied by owner from the actual localhost operator application. Not a replay, seeded fixture or independent GitHub live check. We do **not** publish the screenshot or any secrets in this repository.

Visible observed data:
- One authenticated Perpl Testnet exchange account, **account #1060**.
- Not frozen; order forwarding **OFF**.
- **0** open orders, **0** open positions, **0** order-history entries in first page and **0** first-page fills.
- UI summary: `Aucun changement détecté dans ces agrégats. Cela ne garantit pas l'absence d'incident.`
- Wallet block **69893555**; order-snapshot block **69893556**; position-snapshot block **69893557**.
- `SIGNED PERPL GET / TESTNET / LIVE ACCOUNT SNAPSHOTS`, `LECTURE LIVE OBSERVÉE`, writes disabled.

**Verdict:** Operator LIVE authenticated account read + two-observation no-change comparison **PROVEN via owner screenshot**. These non-atomic blocks do not prove a coherent simultaneous snapshot; absence of open orders is not proof of lack of past submissions or history. Trading/recovery remains unproven.

**Next:** With a genuine order entered on the Perpl Testnet UI or by an already-authorized client, use the READ-only order observer to correlate real `acc + mkt + rq + oid`, exchange status and any fill evidence; do not fabricate requests or enable trading automatically.
