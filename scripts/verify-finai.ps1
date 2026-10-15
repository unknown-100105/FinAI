$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

Push-Location $repoRoot
try {
    Write-Host "=== FinAI final local verification ===" -ForegroundColor Cyan
    Write-Host "Repository: $repoRoot" -ForegroundColor DarkGray
    Write-Host "Python: $python" -ForegroundColor DarkGray

    Write-Host "[1/4] Backend regression" -ForegroundColor Yellow
    & $python -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Backend regression FAILED."
    }

    Write-Host "[2/4] Frontend dependency install" -ForegroundColor Yellow
    Push-Location $frontendRoot
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend npm ci FAILED."
        }

        Write-Host "[3/4] Frontend production build" -ForegroundColor Yellow
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend production build FAILED."
        }

        Write-Host "[4/4] Frontend lint" -ForegroundColor Yellow
        npm run lint
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend lint FAILED."
        }
    }
    finally {
        Pop-Location
    }

    if (-not $env:FINAI_SKIP_LIVE) {
        Write-Host "Live API smoke checks" -ForegroundColor Yellow
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
            throw "Live API checks FAILED: $($_.Exception.Message)"
        }
        Write-Host "Live API checks passed." -ForegroundColor Green
    }
    else {
        Write-Host "Live API checks skipped because FINAI_SKIP_LIVE is set." -ForegroundColor DarkYellow
    }

    Write-Host "Running patent mechanism benchmark..."
    & $python scripts/run_patent_mechanism_benchmark.py --output patent-benchmark.json
    if ($LASTEXITCODE -ne 0) {
        throw "Patent mechanism benchmark failed."
    }

    & $python benchmarks/counterfactual_screening_benchmark.py
    if ($LASTEXITCODE -ne 0) {
        throw "Counterfactual screening benchmark failed."
    }

    Write-Host "=== Verification complete ===" -ForegroundColor Green
}
finally {
    Pop-Location
}
