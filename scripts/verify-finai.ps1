$ErrorActionPreference = "Stop"

Write-Host "=== FinAI final local verification ===" -ForegroundColor Cyan

Write-Host "[1/3] Backend regression" -ForegroundColor Yellow
pytest -q

Write-Host "[2/3] Frontend production build" -ForegroundColor Yellow
Push-Location (Join-Path $PSScriptRoot "..\frontend")
npm run build
Pop-Location

if (-not $env:FINAI_SKIP_LIVE) {
    Write-Host "[3/3] Live API smoke checks" -ForegroundColor Yellow
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
    if ($health.status -ne "ok") { throw "FinAI /health did not return status=ok" }

    $research = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/causal-risk/research-status" -Method Get
    if ($research.status -ne "FINAI_RESEARCH_STACK") { throw "Research status endpoint returned an unexpected status" }

    Write-Host "Live API checks passed." -ForegroundColor Green
}
else {
    Write-Host "Live API checks skipped because FINAI_SKIP_LIVE is set." -ForegroundColor DarkYellow
}

Write-Host "=== Verification complete ===" -ForegroundColor Green