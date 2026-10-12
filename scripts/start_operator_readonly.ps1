# Start the testnet-only operator UI with masked credential entry.
# Credentials remain only in this PowerShell process environment and the local
# child Python process. No logs/files/remote CI receive either secret.
$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

function Get-MaskedInput([string]$label) {
    $s=Read-Host $label -AsSecureString
    $ptr=[IntPtr]::Zero
    try {
        $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
        if($ptr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        }
        $s.Dispose()
    }
}
if(-not (Test-Path "./app.py")) {
    throw "Run from metropolis-perpl-incident-ops repository root."
}
$python=if(Test-Path "./.venv/Scripts/python.exe") {"./.venv/Scripts/python.exe"} else {"python"}
try {
    $env:PERPL_API_KEY_READ=Get-MaskedInput "Perpl Testnet READ API token"
    $env:PERPL_API_KEY_SECRET_READ=Get-MaskedInput "Perpl Ed25519 secret HEX (not wallet seed)"
    if(-not $env:PERPL_API_KEY_READ -or -not $env:PERPL_API_KEY_SECRET_READ) {
        throw "Missing API token or Ed25519 signing secret."
    }
    Write-Host "Opening locally on http://127.0.0.1:8765 (Testnet READ only)."
    Write-Host "Press Ctrl+C to stop server and clear session credentials."
    & $python -m uvicorn app:app --host 127.0.0.1 --port 8765
} finally {
    Remove-Item Env:PERPL_API_KEY_READ -ErrorAction SilentlyContinue
    Remove-Item Env:PERPL_API_KEY_SECRET_READ -ErrorAction SilentlyContinue
}
