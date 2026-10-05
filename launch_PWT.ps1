# launch_PWT.ps1 — ProjWT one-command launcher (Windows / PowerShell)
#
# Does everything: refreshes the Tesla token, starts the signing proxy (if not
# already running), waits for it to listen, sets the env vars, and launches the
# gesture controller against the band. On exit, stops the proxy it started.
#
# Run it:   powershell -ExecutionPolicy Bypass -File launch_PWT.ps1
# or, from the repo root:   .\launch_PWT.ps1
# Then: tap the band once to wake it, do your tap-code (2 taps arm, 2 taps confirm).
#
# ---- EDIT THESE IF YOUR PATHS DIFFER ---------------------------------------
$VIN       = "5YJ3E1EA7JF029858"
$BandAddr  = "D1:86:73:D4:62:86"
$ProxyExe  = "$env:USERPROFILE\vehicle-command\tesla-http-proxy.exe"
$TlsCert   = "$env:USERPROFILE\tls-cert.pem"
$TlsKey    = "$env:USERPROFILE\tls-key.pem"
$SignKey   = "$env:USERPROFILE\private-key.pem"
$ProjSrc   = "$env:USERPROFILE\OneDrive\Documents\GitHub\projwt\src"
$ProxyPort = 4443
# Extra args to gesture_control (tune to taste), e.g. "--strength","2000"
$GestureArgs = @("--backend","tesla")
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

function Test-Port($port) {
    try { (New-Object Net.Sockets.TcpClient).Connect("localhost", $port); return $true }
    catch { return $false }
}

# sanity: required files
foreach ($f in @($ProxyExe, $TlsCert, $TlsKey, $SignKey)) {
    if (-not (Test-Path $f)) { Write-Host "MISSING: $f  (edit the paths at the top of this script)" -ForegroundColor Red; exit 1 }
}

$env:TESLA_VEHICLE_TAG = $VIN
$env:TESLA_FLEET_BASE  = "https://localhost:$ProxyPort"
Set-Location $ProjSrc

Write-Host "== ProjWT launch ==" -ForegroundColor Cyan

# 1. refresh the access token (best-effort; needs TESLA_CLIENT_ID/SECRET set)
Write-Host "Refreshing Tesla token..."
python tesla_auth_PWT.py refresh 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  (refresh skipped — using saved token)" -ForegroundColor Yellow }

# 2. start the signing proxy if it isn't already listening
$proxyProc = $null
if (Test-Port $ProxyPort) {
    Write-Host "Proxy already running on :$ProxyPort."
} else {
    Write-Host "Starting signing proxy on :$ProxyPort ..."
    $proxyProc = Start-Process -FilePath $ProxyExe `
        -ArgumentList @("-tls-key",$TlsKey,"-cert",$TlsCert,"-key-file",$SignKey,"-port","$ProxyPort") `
        -PassThru -WindowStyle Minimized
    for ($i = 0; $i -lt 25; $i++) {
        Start-Sleep -Milliseconds 400
        if (Test-Port $ProxyPort) { break }
    }
    if (-not (Test-Port $ProxyPort)) { Write-Host "Proxy did not start — check cert/key paths." -ForegroundColor Red; exit 1 }
    Write-Host "Proxy up."
}

# 3. launch gesture control
Write-Host ""
Write-Host "Ready. Tap the band once to wake it, then: 2 taps = arm, 2 taps = confirm." -ForegroundColor Green
Write-Host "Ctrl+C to quit.`n"
try {
    python gesture_control_PWT.py $BandAddr @GestureArgs
}
finally {
    if ($proxyProc) {
        Stop-Process -Id $proxyProc.Id -ErrorAction SilentlyContinue
        Write-Host "`nProxy stopped."
    }
}
