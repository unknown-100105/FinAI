$ErrorActionPreference = "Stop"

Write-Host "=== FinAI final local verification ===" -ForegroundColor Cyan

Write-Host "[1/3] Backend regression" -ForegroundColor Yellow
pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend regression FAILED." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "[2/3] Frontend production build" -ForegroundColor Yellow
Push-Location (Join-Path $PSScriptRoot "..\frontend")
npm run build
$frontendExit = $LASTEXITCODE
Pop-Location
if ($frontendExit -ne 0) {
    Write-Host "Frontend production build FAILED." -ForegroundColor Red
    exit $frontendExit
}

if (-not $env:FINAI_SKIP_LIVE) {
    Write-Host "[3/3] Live API smoke checks" -ForegroundColor Yellow
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
        if ($health.status -ne "ok") {
            throw "FinAI /health did not return status=ok"
        }

        $research = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/causal-risk/research-status" -Method Get
        if ($research.status -ne "FINAI_RESEARCH_STACK") {
            throw "Research status endpoint returned an unexpected status"
        }
        if (-not $research.components.temporal_gnn_evaluation) {
            throw "Temporal GNN evaluation capability is missing from research status"
        }
        if (-not $research.components.gflownet_training) {
            throw "GFlowNet research training capability is missing from research status"
        }
        if (-not $research.components.multimodal_encoder) {
            throw "Multimodal encoder capability is missing from research status"
        }

        $architecture = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/causal-risk/architecture" -Method Get
        if ($architecture.status -ne "architecture_implemented") {
            throw "Causal architecture endpoint returned an unexpected status"
        }
    }
    catch {
        Write-Host "Live API checks FAILED: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }

    Write-Host "Live API checks passed." -ForegroundColor Green
}
else {
    Write-Host "Live API checks skipped because FINAI_SKIP_LIVE is set." -ForegroundColor DarkYellow
}

Write-Host "Running patent mechanism benchmark..."
python scripts/run_patent_mechanism_benchmark.py --output patent-benchmark.json
if ($LASTEXITCODE -ne 0) { throw "Patent mechanism benchmark failed" }
Write-Host "=== Verification complete ===" -ForegroundColor Green
