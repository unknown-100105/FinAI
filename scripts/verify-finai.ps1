$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($null -eq $npmCommand) { $npmCommand = Get-Command npm -ErrorAction SilentlyContinue }
if ($null -eq $npmCommand) { throw "npm was not found on PATH. Install Node.js LTS and reopen the shell." }
$npm = $npmCommand.Source
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

# The integrated acceptance runner can select a free loopback port when the default is occupied.
$apiBaseUrl = if (-not [string]::IsNullOrWhiteSpace($env:FINAI_API_BASE_URL)) {
    $env:FINAI_API_BASE_URL.TrimEnd("/")
} else {
    "$apiBaseUrl"
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
        & $npm ci
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend npm ci FAILED."
        }

        Write-Host "[3/4] Frontend production build" -ForegroundColor Yellow
        & $npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend production build FAILED."
        }

        Write-Host "[4/4] Frontend lint" -ForegroundColor Yellow
        & $npm run lint
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend lint FAILED."
        }
    }
    finally {
        Pop-Location
    }

    if (-not $env:FINAI_SKIP_LIVE) {
        Write-Host "Live API smoke checks" -ForegroundColor Yellow
        $apiHeaders = @{}
        if (-not [string]::IsNullOrWhiteSpace($env:FINAI_API_BEARER_TOKEN)) {
            $apiHeaders["Authorization"] = "Bearer $($env:FINAI_API_BEARER_TOKEN)"
        }
        try {
            $health = Invoke-RestMethod -Uri "$apiBaseUrl/health" -Method Get -Headers $apiHeaders
            if ($health.status -ne "ok") {
                throw "FinAI /health did not return status=ok"
            }

            $apiInfo = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1" -Method Get -Headers $apiHeaders
            if ($apiInfo.endpoints.brain_status -ne "/api/v1/system/brain-status") {
                throw "FinAI API info does not advertise the Brain status endpoint"
            }
            if ($apiInfo.endpoints.xai -ne "/api/v1/xai") {
                throw "FinAI API info has an invalid XAI endpoint"
            }

            $models = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/models" -Method Get -Headers $apiHeaders
            if ($null -eq $models.models -or $models.models.Count -lt 1) {
                throw "Model registry endpoint returned no model definitions"
            }
            foreach ($model in $models.models) {
                if ([string]::IsNullOrWhiteSpace([string]$model.model_id) -or
                    [string]::IsNullOrWhiteSpace([string]$model.provider) -or
                    $null -eq $model.enabled -or $null -eq $model.configured) {
                    throw "Model registry contains an incomplete model definition"
                }
            }

            $brain = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/system/brain-status" -Method Get -Headers $apiHeaders
            if ($brain.status -ne "diagnostic") {
                throw "FinAI Brain status endpoint returned an unexpected status"
            }
            if ($brain.live_checks_performed -ne $false) {
                throw "Brain diagnostics must explicitly report that live checks were not performed"
            }
            if ($brain.security.shared_token_value_exposed -ne $false) {
                throw "Brain diagnostics must never expose the API bearer token"
            }

            # Configuration-only local-model diagnostic: this must never probe a server.
            $localModel = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/system/local-model-status" -Method Get -Headers $apiHeaders
            if ($localModel.probe_requested -ne $false -or $localModel.reachable -ne $false) {
                throw "Default local-model status unexpectedly performed a network probe or claimed reachability"
            }
            if ($localModel.status -notin @("unconfigured", "configured_not_probed", "invalid_configuration")) {
                throw "Local-model diagnostic returned an unexpected configuration-only status: $($localModel.status)"
            }

            # Retrieval Lab compare mode is local-only and must return a graceful result
            # for both engines, whether approved RAG artifacts are present or absent.
            $retrievalBody = @{
                query = "budget planning"
                mode = "compare"
                top_k = 3
            } | ConvertTo-Json -Compress
            $retrieval = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/retrieval-lab/search" -Method Post -Headers $apiHeaders -ContentType "application/json" -Body $retrievalBody
            if ($retrieval.mode -ne "compare" -or $null -eq $retrieval.results_by_mode) {
                throw "Retrieval Lab compare endpoint returned an invalid response shape"
            }
            foreach ($retrievalMode in @("vectorless", "hybrid")) {
                $modeResult = $retrieval.results_by_mode.$retrievalMode
                if ($null -eq $modeResult -or $modeResult.mode -ne $retrievalMode) {
                    throw "Retrieval Lab did not return the expected $retrievalMode result"
                }
                if ($modeResult.status -notin @("available", "unavailable", "error")) {
                    throw "Retrieval Lab $retrievalMode returned an undocumented status: $($modeResult.status)"
                }
                if ([int]$modeResult.result_count -lt 0) {
                    throw "Retrieval Lab $retrievalMode returned an invalid result count"
                }
            }

            $research = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/causal-risk/research-status" -Method Get -Headers $apiHeaders
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

            $architecture = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/causal-risk/architecture" -Method Get -Headers $apiHeaders
            if ($architecture.status -ne "architecture_implemented") {
                throw "Causal architecture endpoint returned an unexpected status"
            }

            $swarmtrade = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/swarmtrade/status" -Method Get -Headers $apiHeaders
            if ($swarmtrade.status -ne "available" -or $swarmtrade.max_logical_agents -ne 500) {
                throw "SwarmTrade status endpoint returned an unexpected response"
            }
            if ($swarmtrade.live_order_execution -ne $false) {
                throw "SwarmTrade status must explicitly disable live order execution"
            }

            $swarmPlanBody = @{
                symbol = "FINAI-SMOKE"
                asset_class = "equity"
                side = "auto"
                entry_price = 100
                stop_price = 95
                target_price = 112
                capital = 100000
                risk_pct = 0.5
                max_leverage = 2
                margin_rate = 0.1
                fee_bps = 5
                slippage_bps = 5
                agent_count = 500
                signals = @{
                    trend = 0.9
                    momentum = 0.8
                    mean_reversion = 0.1
                    breakout = 0.8
                    sentiment = 0.7
                }
            } | ConvertTo-Json -Depth 6 -Compress
            $swarmPlan = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/swarmtrade/plan" -Method Post -Headers $apiHeaders -ContentType "application/json" -Body $swarmPlanBody
            if ($swarmPlan.status -ne "APPROVED_FOR_SIMULATION") {
                throw "Synthetic SwarmTrade plan did not pass expected risk gates: $($swarmPlan.reason)"
            }
            if ($swarmPlan.agent_count -ne 500 -or $swarmPlan.execution.order_submitted -ne $false -or $swarmPlan.execution.fill_claimed -ne $false) {
                throw "SwarmTrade simulation smoke request violated an execution boundary"
            }
            if ($swarmPlan.risk.effective_risk_pct -gt 1.0 -or $swarmPlan.risk.estimated_total_risk -gt $swarmPlan.risk.risk_budget) {
                throw "SwarmTrade simulation smoke request violated position risk limits"
            }

            $researchControl = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/causal-risk/research-control/status" -Method Get -Headers $apiHeaders
            if ($researchControl.status -ne "available" -or $researchControl.can_authorize_trades -ne $false) {
                throw "Research control endpoint returned an unexpected response or trade boundary"
            }

            $paperLedger = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/swarmtrade/paper/status" -Method Get -Headers $apiHeaders
            if ($paperLedger.mode -ne "persistent_paper_trading_only" -or $paperLedger.real_orders_supported -ne $false) {
                throw "Paper ledger status did not confirm simulation-only operation"
            }

            # Exercise a real request path without requiring cloud credentials or model inference.
            $sessionId = "finai-live-smoke-$([guid]::NewGuid().ToString('N'))"
            $chatBody = @{
                session_id = $sessionId
                message = "How much is my account balance?"
                generate_response = $false
            } | ConvertTo-Json -Compress
            $chat = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/chat" -Method Post -Headers $apiHeaders -ContentType "application/json" -Body $chatBody
            if ($chat.session_id -ne $sessionId) {
                throw "Chat endpoint did not preserve the supplied smoke-test session ID"
            }
            if ($chat.status -ne "AUTH_REQUIRED") {
                throw "Safe account-balance smoke request did not stop at the expected authentication boundary"
            }
            if ([string]::IsNullOrWhiteSpace([string]$chat.trace_id)) {
                throw "Chat smoke request did not return a trace ID"
            }

            $xai = Invoke-RestMethod -Uri "$apiBaseUrl/api/v1/xai/traces" -Method Get -Headers $apiHeaders
            if ($null -eq $xai.traces -or $null -eq $xai.count) {
                throw "XAI traces endpoint returned an unexpected response shape"
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

    Write-Host "Running local preflight..." -ForegroundColor Yellow
    & $python scripts/finai_preflight.py
    if ($LASTEXITCODE -ne 0) {
        throw "FinAI preflight failed."
    }

    Write-Host "Checking provider configuration without network calls..." -ForegroundColor Yellow
    & $python scripts/smoke_llm_providers.py
    if ($LASTEXITCODE -ne 0) {
        throw "Provider configuration check failed."
    }

    if ($env:FINAI_RUN_LIVE_PROVIDER_SMOKE -in @("1", "true", "yes", "on")) {
        Write-Host "Running opt-in live provider smoke tests (may incur API charges)..." -ForegroundColor Yellow
        & $python scripts/smoke_llm_providers.py --live
        if ($LASTEXITCODE -ne 0) {
            throw "One or more configured live LLM provider smoke tests failed."
        }
    }
    else {
        Write-Host "Live LLM provider calls skipped. Set FINAI_RUN_LIVE_PROVIDER_SMOKE=1 to opt in." -ForegroundColor DarkYellow
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

    Write-Host "Running seeded SwarmTrade safety benchmark..." -ForegroundColor Yellow
    & $python benchmarks/swarmtrade_safety_benchmark.py --output swarmtrade-safety-benchmark.json --cases 500
    if ($LASTEXITCODE -ne 0) {
        throw "SwarmTrade safety benchmark failed."
    }

    Write-Host "=== Verification complete ===" -ForegroundColor Green
}
finally {
    Pop-Location
}
