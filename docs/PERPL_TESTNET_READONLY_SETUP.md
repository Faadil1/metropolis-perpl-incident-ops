# Perpl Testnet — Owner-Side Read-Only Setup

**Do this on your own computer, not in a chat message, issue, PR or CI secret.**
A public API probe is not an authenticated testnet read, and neither is a trading session.

## 1. Resolve Perpl UI prerequisite (observed in user's Testnet screenshot, 2026-10-10)

The page `https://testnet.perpl.xyz/apikeys` displayed:

> You need to deposit funds to create a trading account before you can create API keys.
> Sign in pending

This is a **Web UI enrollment prerequisite**. Canonical Perpl API documentation treats *API enrollment*, *Exchange account creation*, and *order forwarding* as distinct components. **The API enrollment protocol does not, by itself, prove an Exchange account or any right to trade.** Do not claim that the UI allows a key before depositing; the observed UI blocks it.

1. Confirm URL is `testnet.perpl.xyz` and wallet network is **Monad Testnet chain ID 10143**, using a *dedicated throwaway test wallet*.
2. Click **Sign in pending** once, inspect the browser wallet's pending request; only approve a normal Perpl sign-in message after verifying origin and scope. If it asks for unlimited token allowance, a transfer, or mainnet rights, **stop and inspect**.
3. Navigate to the Perpl Testnet trading/account view and look for **Deposit / Deposit to Enable Trading** (official docs say this is the Web UI route for creating an exchange account). Do not guess the needed amount: check the UI and live public `/api/v1/pub/context` account-open limits.
4. Obtain test MON for gas from the [official Monad faucet](https://faucet.monad.xyz) if needed. **MON is gas, not the Perpl collateral token.**
5. For the required testnet collateral, use only the token shown by the live Perpl Testnet interface, and validate its FULL contract address in MetaMask. **Observed UI on 2026-10-10**: 10,000 test AUSD available, minimum deposit 100 AUSD, approval cap 100 AUSD, token truncated `0xa9012…322dC`, spender `0x1964C…080cc`. Independent integration [PerplBot](https://github.com/0x70626a/PerplBot/blob/main/README.md) lists testnet collateral token `0xa9012a055bd4e0eDfF8Ce09f960291C09D5322dC` and Perpl Exchange `0x1964C32f0bE608E7D29302AFF5E61268E72080cc`. **Important documentation conflict:** [Perpl's API README](https://github.com/PerplFoundation/api-docs/blob/main/README.md#network-configuration) lists an older/different testnet collateral, USD `0xdf5b718d8fcc173335185a2a1513ee8151e3c027`. This is not evidence that the UI token is illegitimate; confirm the full addresses and live chain 10143 before signing, and never infer a full address solely from a shortened display.
6. Any token approval must be limited to the actual test deposit amount; inspect the target contract and chain before confirming. **No actual funds, mainnet bridge, unlimited approvals or use of the user's primary wallet.**
7. After a successful test-only deposit and account creation, return to API Keys; enroll a **read-only** key and store its opaque token and Ed25519 secret *locally*. Do not grant `trade`; do not enable One-Click Trading or `allowOrderForwarding(true)` for read-only inspection.

**If no trustworthy test collateral faucet is available:** STOP. This is an **EXTERNAL_ACCOUNT_BOOTSTRAP_BLOCKED** condition; do not purchase tokens or relabel a local fixture as live. A programmatic read-key enrollment flow is documented at [Perpl Integrations](https://github.com/PerplFoundation/api-docs/blob/main/integrations.md) and may avoid the *frontend enrollment gate*, but cannot create a funded Exchange account or prove the live operator workflow.

Sources: [Perpl API documentation](https://github.com/PerplFoundation/api-docs/blob/main/README.md), [Perpl Authentication](https://github.com/PerplFoundation/api-docs/blob/main/authentication.md), [Monad official testnet faucet](https://faucet.monad.xyz).

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
