# Perpl Testnet owner-only credential entry. No key may enter shell history,
# terminal echo, file, PR or GitHub Actions. Read-only testnet calls only.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Read-SecretText([string] $Label) {
    $secure = Read-Host $Label -AsSecureString
    $ptr = [IntPtr]::Zero
    try {
        $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
        if ($ptr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        }
        $secure.Dispose()
    }
}

if (-not (Test-Path "./perpl_auth_check.py")) {
    throw "Exécuter depuis la racine du dépôt metropolis-perpl-incident-ops"
}
$python = if (Test-Path "./.venv/Scripts/python.exe") {
    "./.venv/Scripts/python.exe"
} else { "python" }

try {
    $env:PERPL_API_KEY_READ = Read-SecretText "Token API Perpl READ (saisie masquée)"
    $env:PERPL_API_KEY_SECRET_READ = Read-SecretText "Secret Ed25519 HEX (saisie masquée; PAS la phrase de récupération)"
    if (-not $env:PERPL_API_KEY_READ -or -not $env:PERPL_API_KEY_SECRET_READ) {
        throw "Le token ou le secret de signature est vide."
    }
    Write-Host "Lecture authentifiée READ Perpl Testnet uniquement. Aucun ordre ni retrait."
    & $python "perpl_auth_check.py"
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Warning "La vérification n'est pas entièrement concluante. Aucun ordre n'a été transmis."
    } else {
        Write-Host "Readiness READ confirmé. Le produit LIVE complet reste non prouvé."
    }
} finally {
    Remove-Item Env:PERPL_API_KEY_READ -ErrorAction SilentlyContinue
    Remove-Item Env:PERPL_API_KEY_SECRET_READ -ErrorAction SilentlyContinue
}
