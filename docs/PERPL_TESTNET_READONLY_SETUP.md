# Perpl Testnet — Owner-Side Read-Only Setup

**Do this on your own computer, not in a chat message, issue, PR or CI secret.**
A public API probe is not an authenticated testnet read, and neither is a trading session.

## 1. Enroll a strictly READ-scoped key
1. Open the [official Perpl Testnet API Keys page](https://testnet.perpl.xyz/apikeys).
2. Connect **a dedicated test wallet**. Do not use your primary wallet or transfer mainnet funds.
3. Select **read-only** scope, not `trade` or a combined scope.
4. Create the key by wallet signing as instructed on that page.
5. Keep the opaque `X-API-Key` token and the Ed25519 secret on your machine.

Official guide: [Perpl Quickstart](https://github.com/PerplFoundation/perpl-docs/blob/main/docs/resources/for-developers/quickstart.md). Enrolling a key alone **does not** create an exchange account. Some per-account reads can return 404 until a testnet Exchange account is created separately.

## 2. Configure LOCAL environment variables

PowerShell (Windows — terminal session only):
```powershell
$env:PERPL_API_KEY_READ = "YOUR_LOCAL_READ_TOKEN"
$env:PERPL_API_KEY_SECRET_READ = "YOUR_LOCAL_ED25519_KEY_HEX"
$env:INCIDENT_DB_PATH = ".\\runtime\\incidents.sqlite3"
```
Do not copy these values into a screenshot or send them to anyone.

## 3. Start local app from this repository's research branch
```powershell
git clone https://github.com/Faadil1/metropolis-perpl-incident-ops.git
cd metropolis-perpl-incident-ops
git switch research/live-depth-foundation
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765`. Create an incident using your *own* real Perpl account and `rq` only if available, then press **Lire Perpl Testnet (clé READ)**. This performs GET calls and records snapshots; it does **not** execute or cancel any order.

## 4. Read the result honestly
- `404` can mean no on-chain Perpl exchange account exists; it does not prove an outage.
- `401/403` may mean wrong key, scope, signature or timestamp.
- Lost connectivity means UNKNOWN; the application must not issue a new order to guess.
- An empty authenticated order list does not prove that an uncertain order never filled. Order history/fills must be reconciled before a terminal claim.
- Even a successful testnet public read does **not** prove an incident or a full core business loop.
- No real-money or mainnet operations are authorized in this project.

## 5. Current blocking work
- Compare against the *current* Desk `OrderTracker` and PerplBot, not only their historical bug.
- Verify `rq`/account semantics in real authenticated frames.
- Implement immutable-attempt idempotency and authenticated reconciliation across order and fill history.
- Keep exchange writes disabled until bounded owner authority, authorization, and post-action checks are proven.
