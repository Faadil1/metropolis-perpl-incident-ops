# First real Perpl Testnet order — operator-verified aggregate change

Date: **2026-10-10**. Proof class: `OWNER_SCREENSHOTS_LIVE_PERPL_UI_PLUS_SIGNED_LOCAL_OPERATOR_COUNTS`.

## Exchange UI observation

- Venue: Perpl Testnet, BTC perpetual contract, account #1060.
- A genuine **Limit Long / Post Only / 1×** order is listed as **OPEN** by the venue.
- Price: **82,000 USD**, size: **0.0002 BTC**, original and remaining size both 0.0002 BTC, notional **16.40 test USD**.
- Order was placed through the actual Perpl site by the owner, not by Metropolis.
- **No order `rq` or `oid` visible** in the screenshot, so those identifiers remain unknown.

## Local Metropolis authenticated UI observation

- Signed HTTP testnet account refresh shows **1 open order**, **1 event on the first history page**, **0 fills**, **0 open positions**.
- Classification: change observed between two reads; examination needed, **not proof of an error, fill or incident**.
- Blocks: wallet **69900670**, orders **69900671**, positions **69900672**, deliberately non-atomic.
- Local app had **0 incidents**, no exchange write capability and no actual recovery.
- Local operator screenshot did *not* display the new **Ordres réellement observés** panel; probably still running earlier checked-out code. Must restart after pulling latest branch.

## Evidence and permission boundaries

Neither screenshot is published to this public repo. No wallet address, API token, Ed25519 secret, signing information or raw account payload has been provided or retained. Aggregate and order metadata listed here come only from the owner's screenshots.

**Positive path PROVEN:** Real testnet order placed in venue UI → local authenticated Perpl API counts observed one open order.

**Still pending:** new row observer verifies exact `acc + mkt + rq + oid + st`; later safe cancellation on official venue and independently verified state transition; event/position reconciliation, genuine incident/recovery and unmet market need. A visible open order may fill at any time. Do not create a duplicate order or imply the core product is finished.
