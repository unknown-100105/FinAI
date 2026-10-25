#requires -Version 5.1
<#
.SYNOPSIS
Runs the full FinAI local acceptance pass with an isolated paper-ledger API.
.DESCRIPTION
Runs the backend/frontend/preflight/provider-config/benchmark verifier, starts a temporary loopback API with a fresh paper SQLite database, and verifies the paper account open/replay/conflict/close/history workflow. It never calls paid LLM providers and explicitly disables live execution.
#>
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }
$port = 8000
$frontendPort = 5173
$baseUrl = "http://127.0.0.1:$port"
$timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss-fff")
$outputRoot = Join-Path $repoRoot "verification-output"
$runDir = Join-Path $outputRoot $timestamp
$stdoutPath = Join-Path $runDir "api.stdout.log"
$stderrPath = Join-Path $runDir "api.stderr.log"
$frontendStdoutPath = Join-Path $runDir "frontend-dev.stdout.log"
$frontendStderrPath = Join-Path $runDir "frontend-dev.stderr.log"
$paperDbPath = Join-Path $runDir "paper-ledger.sqlite3"
$haltFilePath = Join-Path $runDir "paper-entries.halt"
$summaryPath = Join-Path $runDir "verification-report.json"
$preflightPath = Join-Path $runDir "preflight.json"
$apiProcess = $null
$frontendProcess = $null
$stageResults = [System.Collections.Generic.List[object]]::new()
$startedAt = [DateTime]::UtcNow.ToString("o")
$originalEnvironment = @{}
$environmentNames = @("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "FINAI_SWARMTRADE_PAPER_DB", "FINAI_LIVE_TRADING_ENABLED", "FINAI_SKIP_LIVE", "FINAI_RUN_LIVE_PROVIDER_SMOKE", "FINAI_SWARMTRADE_PAPER_ENTRIES_HALTED", "FINAI_SWARMTRADE_PAPER_HALT_FILE", "FINAI_API_BASE_URL", "FINAI_CORS_ALLOW_ORIGINS", "VITE_API_BASE_URL")

New-Item -ItemType Directory -Path $runDir -Force | Out-Null
foreach ($name in $environmentNames) { $originalEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process") }

function Get-AvailableLoopbackPort {
    param([Parameter(Mandatory = $true)][int]$PreferredPort)

    $preferred = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $PreferredPort)
    try {
        $preferred.Start()
        return $PreferredPort
    } catch {
        # An existing service may be using the default port; fall back to an OS-assigned port.
    } finally {
        if ($null -ne $preferred) { $preferred.Stop() }
    }

    $dynamic = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    try {
        $dynamic.Start()
        return ([System.Net.IPEndPoint]$dynamic.LocalEndpoint).Port
    } finally {
        if ($null -ne $dynamic) { $dynamic.Stop() }
    }
}

function Add-StageResult {
    param([string]$Name, [string]$Status, [string]$Details)
    $stageResults.Add([pscustomobject]@{ name = $Name; status = $Status; details = $Details; recorded_at_utc = [DateTime]::UtcNow.ToString("o") })
}

function Invoke-ApiJson {
    param([Parameter(Mandatory = $true)][string]$Method, [Parameter(Mandatory = $true)][string]$Path, $Body = $null)
    $headers = @{}
    if (-not [string]::IsNullOrWhiteSpace($env:FINAI_API_BEARER_TOKEN)) { $headers["Authorization"] = "Bearer $($env:FINAI_API_BEARER_TOKEN)" }
    if ($null -eq $Body) { return Invoke-RestMethod -Uri "$baseUrl$Path" -Method $Method -Headers $headers -TimeoutSec 10 }
    $json = $Body | ConvertTo-Json -Depth 12 -Compress
    return Invoke-RestMethod -Uri "$baseUrl$Path" -Method $Method -Headers $headers -ContentType "application/json" -Body $json -TimeoutSec 10
}

try {
    Write-Host "=== FinAI full local acceptance run ===" -ForegroundColor Cyan
    Write-Host "Repository: $repoRoot"
    Write-Host "Output: $runDir"
    Write-Host "Python: $python"
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "npm was not found on PATH. Install Node.js LTS, reopen PowerShell, and rerun." }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git was not found on PATH." }

    Push-Location $repoRoot
    try {
        $head = (& git rev-parse HEAD).Trim()
        $branchName = (& git branch --show-current).Trim()
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($head)) { throw "Could not determine the current Git commit." }

        # Prefer conventional ports, but automatically use free loopback ports when another service is running.
        $port = Get-AvailableLoopbackPort -PreferredPort 8000
        $frontendPort = Get-AvailableLoopbackPort -PreferredPort 5173
        $baseUrl = "http://127.0.0.1:$port"
        $frontendOrigin = "http://127.0.0.1:$frontendPort"
        [Environment]::SetEnvironmentVariable("FINAI_API_BASE_URL", $baseUrl, "Process")
        [Environment]::SetEnvironmentVariable("FINAI_CORS_ALLOW_ORIGINS", $frontendOrigin, "Process")
        # Keep the production build's API URL independent of this run's ephemeral port;
        # set VITE_API_BASE_URL only for the dev-server smoke process below.
        [Environment]::SetEnvironmentVariable("VITE_API_BASE_URL", $null, "Process")
        Write-Host "API port: $port ; frontend port: $frontendPort"

        [Environment]::SetEnvironmentVariable("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1", "Process")
        [Environment]::SetEnvironmentVariable("FINAI_SWARMTRADE_PAPER_DB", $paperDbPath, "Process")
        [Environment]::SetEnvironmentVariable("FINAI_LIVE_TRADING_ENABLED", "0", "Process")
        [Environment]::SetEnvironmentVariable("FINAI_SKIP_LIVE", $null, "Process")
        $liveProviderSmoke = [string]$originalEnvironment["FINAI_RUN_LIVE_PROVIDER_SMOKE"]
        if ($liveProviderSmoke -in @("1", "true", "yes", "on")) {
            [Environment]::SetEnvironmentVariable("FINAI_RUN_LIVE_PROVIDER_SMOKE", $liveProviderSmoke, "Process")
        } else {
            [Environment]::SetEnvironmentVariable("FINAI_RUN_LIVE_PROVIDER_SMOKE", "0", "Process")
        }
        [Environment]::SetEnvironmentVariable("FINAI_SWARMTRADE_PAPER_ENTRIES_HALTED", "0", "Process")
        [Environment]::SetEnvironmentVariable("FINAI_SWARMTRADE_PAPER_HALT_FILE", $haltFilePath, "Process")

        Write-Host "[API] Starting isolated loopback API..." -ForegroundColor Yellow
        $apiProcess = Start-Process -FilePath $python -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port $port" -WorkingDirectory $repoRoot -PassThru -NoNewWindow -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
        $healthy = $false
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            $apiProcess.Refresh()
            if ($apiProcess.HasExited) {
                $tail = if (Test-Path $stderrPath) { (Get-Content $stderrPath -Tail 80) -join [Environment]::NewLine } else { "No stderr log was written." }
                throw "Local API process exited during startup. Logs: $stderrPath. $tail"
            }
            try {
                $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 2
                if ($health.status -eq "ok") { $healthy = $true; break }
            } catch { Start-Sleep -Seconds 1 }
        }
        if (-not $healthy) {
            $tail = if (Test-Path $stderrPath) { (Get-Content $stderrPath -Tail 80) -join [Environment]::NewLine } else { "No stderr log was written." }
            throw "Local API did not become healthy within 60 seconds. Logs: $stderrPath. $tail"
        }
        Add-StageResult "isolated_api_startup" "passed" "Loopback API returned /health status=ok; paper ledger uses a new run-specific SQLite database."

        # The API process already inherited the isolated paper settings. Clear these
        # variables in the parent so pytest evaluates the normal safe defaults and
        # cannot accidentally share the API smoke-test database.
        [Environment]::SetEnvironmentVariable("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "0", "Process")
        [Environment]::SetEnvironmentVariable("FINAI_SWARMTRADE_PAPER_DB", "", "Process")
        [Environment]::SetEnvironmentVariable("FINAI_SWARMTRADE_PAPER_ENTRIES_HALTED", "0", "Process")
        [Environment]::SetEnvironmentVariable("FINAI_SWARMTRADE_PAPER_HALT_FILE", "", "Process")

        Write-Host "[FULL] Backend, frontend, API, preflight, provider configuration and benchmarks..." -ForegroundColor Yellow
        & (Join-Path $repoRoot "scripts\verify-finai.ps1")
        if ($LASTEXITCODE -ne 0) { throw "scripts/verify-finai.ps1 returned exit code $LASTEXITCODE." }
        Add-StageResult "existing_full_verifier" "passed" "verify-finai.ps1 completed backend tests, frontend npm ci/build/lint, API smoke checks, provider configuration, patent mechanism, counterfactual screening, and SwarmTrade safety benchmarks."

        Write-Host "[FRONTEND] Starting built Vite application for a local HTTP smoke check..." -ForegroundColor Yellow
        $frontendProbe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $frontendPort)
        try { $frontendProbe.Start() }
        catch { throw "Frontend port $frontendPort is already in use. Stop the service using 127.0.0.1:$frontendPort and rerun." }
        finally { $frontendProbe.Stop() }
        $commandProcessor = if (-not [string]::IsNullOrWhiteSpace($env:ComSpec)) { $env:ComSpec } else { Join-Path $env:SystemRoot "System32\cmd.exe" }
        $frontendRoot = Join-Path $repoRoot "frontend"
        [Environment]::SetEnvironmentVariable("VITE_API_BASE_URL", $baseUrl, "Process")
        $frontendProcess = Start-Process -FilePath $commandProcessor -ArgumentList "/d /c npm.cmd run dev -- --host 127.0.0.1 --port $frontendPort --strictPort" -WorkingDirectory $frontendRoot -PassThru -NoNewWindow -RedirectStandardOutput $frontendStdoutPath -RedirectStandardError $frontendStderrPath
        $frontendHealthy = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            $frontendProcess.Refresh()
            if ($frontendProcess.HasExited) {
                $tail = if (Test-Path $frontendStderrPath) { (Get-Content $frontendStderrPath -Tail 60) -join [Environment]::NewLine } else { "No frontend stderr log." }
                throw "Vite dev server exited during startup. Logs: $frontendStdoutPath ; $frontendStderrPath. $tail"
            }
            try {
                $frontendResponse = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$frontendPort/" -Method Get -TimeoutSec 2
                if ([int]$frontendResponse.StatusCode -eq 200) { $frontendHealthy = $true; break }
            } catch { Start-Sleep -Seconds 1 }
        }
        if (-not $frontendHealthy) { throw "Vite did not return HTTP 200 within 30 seconds. Inspect $frontendStdoutPath and $frontendStderrPath." }
        Add-StageResult "frontend_dev_server" "passed" "Vite dev server returned HTTP 200 on loopback after the production build; child will be stopped during cleanup."

        Write-Host "[PAPER] Checking safety boundary..." -ForegroundColor Yellow
        $safety = Invoke-ApiJson -Method Get -Path "/api/v1/swarmtrade/safety/status"
        if ($safety.live_execution_enabled -ne $false -or $safety.broker_connected -ne $false -or $safety.order_submission_supported -ne $false) {
            throw "Safety status did not explicitly keep live execution, broker connection, and order submission disabled."
        }
        $paperStatus = Invoke-ApiJson -Method Get -Path "/api/v1/swarmtrade/paper/status"
        if ($paperStatus.enabled -ne $true -or $paperStatus.real_orders_supported -ne $false) { throw "Paper ledger is not enabled for this isolated process or reports live-order capability." }
        Add-StageResult "trading_safety_boundary" "passed" "No broker, no order submission; paper API reports simulation-only mode."

        Write-Host "[PAPER] Exercising account, open, replay, conflict, close and history..." -ForegroundColor Yellow
        $account = Invoke-ApiJson -Method Post -Path "/api/v1/swarmtrade/paper/accounts" -Body @{ label = "FinAI isolated verification"; currency = "USD"; initial_capital = 100000 }
        $accountId = [string]$account.account_id
        if ([string]::IsNullOrWhiteSpace($accountId)) { throw "Paper account creation returned no account_id." }

        $openRequest = @{
            idempotency_key = "verify-open-$([guid]::NewGuid().ToString('N'))"
            quote_currency = "USD"
            acknowledge_simulation_only = $true
            plan = @{
                symbol = "FINAI-VERIFY"; asset_class = "equity"; side = "auto"
                entry_price = 100; stop_price = 95; target_price = 112; capital = 100000
                risk_pct = 0.5; max_leverage = 2; margin_rate = 0.1; fee_bps = 5; slippage_bps = 5; agent_count = 500
                signals = @{ trend = 0.9; momentum = 0.8; mean_reversion = 0.1; breakout = 0.8; sentiment = 0.7 }
            }
        }
        $openPath = "/api/v1/swarmtrade/paper/accounts/$accountId/positions"
        $opened = Invoke-ApiJson -Method Post -Path $openPath -Body $openRequest
        if ($opened.status -ne "PAPER_POSITION_OPEN" -or $opened.execution.real_order_submitted -ne $false -or $opened.execution.simulated_entry_recorded -ne $true) {
            throw "Paper open response failed simulation-only assertions."
        }
        $openedReplay = Invoke-ApiJson -Method Post -Path $openPath -Body $openRequest
        if ($openedReplay.idempotent_replay -ne $true -or $openedReplay.position_id -ne $opened.position_id) { throw "Same-key/same-payload open retry did not replay the original position." }

        $conflictingRequest = @{ idempotency_key = $openRequest.idempotency_key; quote_currency = "USD"; acknowledge_simulation_only = $true; plan = @{} }
        foreach ($key in $openRequest.plan.Keys) { $conflictingRequest.plan[$key] = $openRequest.plan[$key] }
        $conflictingRequest.plan.target_price = 113
        $conflictStatus = $null
        try {
            $null = Invoke-ApiJson -Method Post -Path $openPath -Body $conflictingRequest
            throw "Conflicting payload reused an idempotency key but unexpectedly succeeded."
        } catch {
            if ($_.Exception.Message -like "*unexpectedly succeeded*") { throw }
            try { $conflictStatus = [int]$_.Exception.Response.StatusCode } catch { $conflictStatus = $null }
            if ($conflictStatus -ne 409) { throw "Conflicting idempotency payload should return HTTP 409; observed '$conflictStatus'. Original error: $($_.Exception.Message)" }
        }

        # Activate the operator-controlled paper entry halt without restarting the API.
        New-Item -ItemType File -Path $haltFilePath -Force | Out-Null
        $haltStatus = Invoke-ApiJson -Method Get -Path "/api/v1/swarmtrade/paper/status"
        if ($haltStatus.new_entries_halted -ne $true) { throw "Paper entry-halt sentinel did not appear in status." }
        $haltedReplay = Invoke-ApiJson -Method Post -Path $openPath -Body $openRequest
        if ($haltedReplay.idempotent_replay -ne $true -or $haltedReplay.position_id -ne $opened.position_id) {
            throw "Entry halt broke an idempotent replay of an already successful paper open."
        }
        $haltedOpen = @{
            idempotency_key = "verify-halted-open-$([guid]::NewGuid().ToString('N'))"
            quote_currency = "USD"
            acknowledge_simulation_only = $true
            plan = $openRequest.plan
        }
        $haltResponseStatus = $null
        try {
            $null = Invoke-ApiJson -Method Post -Path $openPath -Body $haltedOpen
            throw "New paper position unexpectedly succeeded while entry halt was active."
        } catch {
            if ($_.Exception.Message -like "*unexpectedly succeeded*") { throw }
            try { $haltResponseStatus = [int]$_.Exception.Response.StatusCode } catch { $haltResponseStatus = $null }
            if ($haltResponseStatus -ne 423) { throw "Entry halt should reject new simulated positions with HTTP 423; observed '$haltResponseStatus'." }
        }
        Add-StageResult "paper_entry_halt" "passed" "Operator halt sentinel blocks new paper entries with HTTP 423 while preserving the ability to close the existing paper position."

        $positionId = [string]$opened.position_id
        $closePath = "/api/v1/swarmtrade/paper/accounts/$accountId/positions/$positionId/close"
        $closeRequest = @{ idempotency_key = "verify-close-$([guid]::NewGuid().ToString('N'))"; exit_price = 115; reason = "manual" }
        $closed = Invoke-ApiJson -Method Post -Path $closePath -Body $closeRequest
        if ($closed.status -ne "PAPER_POSITION_CLOSED" -or $closed.execution.real_order_submitted -ne $false) { throw "Paper close response failed simulation-only assertions." }
        $closedReplay = Invoke-ApiJson -Method Post -Path $closePath -Body $closeRequest
        if ($closedReplay.idempotent_replay -ne $true -or $closedReplay.position_id -ne $positionId) { throw "Same-key/same-payload close retry did not replay the original close." }

        $accountAfter = Invoke-ApiJson -Method Get -Path "/api/v1/swarmtrade/paper/accounts/$accountId"
        $history = Invoke-ApiJson -Method Get -Path "/api/v1/swarmtrade/paper/accounts/$accountId/positions?status=closed"
        if ($accountAfter.open_position_count -ne 0 -or $history.count -ne 1 -or $history.positions[0].position_id -ne $positionId -or $null -eq $accountAfter.realized_pnl) {
            throw "Paper account snapshot/closed history did not reconcile after the simulated round trip."
        }
        Remove-Item -LiteralPath $haltFilePath -Force -ErrorAction SilentlyContinue
        $resumedStatus = Invoke-ApiJson -Method Get -Path "/api/v1/swarmtrade/paper/status"
        if ($resumedStatus.new_entries_halted -ne $false) { throw "Paper entry halt remained active after removing its sentinel." }
        Add-StageResult "paper_ledger_api_round_trip" "passed" "Account create; simulated open; same-payload replay; conflicting-key HTTP 409; close despite halt; close replay; realized P&L and closed history; entry resumption after halt removal."

        Write-Host "[BENCHMARK] Validating machine-readable SwarmTrade output..." -ForegroundColor Yellow
        $swarmReportPath = Join-Path $repoRoot "swarmtrade-safety-benchmark.json"
        if (-not (Test-Path $swarmReportPath)) { throw "Expected benchmark output was not written: $swarmReportPath" }
        $swarmReport = Get-Content $swarmReportPath -Raw | ConvertFrom-Json
        foreach ($field in @("failure_count", "determinism_failures", "expected_control_rejections_missed", "expected_feasible_approval_missed", "guardrail_violations")) {
            if ([int]$swarmReport.$field -ne 0) { throw "SwarmTrade benchmark field '$field' was $($swarmReport.$field), expected zero." }
        }
        if ([int]$swarmReport.passed_cases -ne [int]$swarmReport.cases) { throw "SwarmTrade benchmark passed_cases ($($swarmReport.passed_cases)) did not equal cases ($($swarmReport.cases))." }
        Add-StageResult "swarmtrade_benchmark_assertions" "passed" "$($swarmReport.passed_cases)/$($swarmReport.cases) synthetic deterministic cases; zero reported failures and guardrail violations."

        Write-Host "[BENCHMARK] Validating patent mechanism correctness report..." -ForegroundColor Yellow
        $patentReportPath = Join-Path $repoRoot "patent-benchmark.json"
        if (-not (Test-Path $patentReportPath)) { throw "Expected patent mechanism report was not written: $patentReportPath" }
        $patentReport = Get-Content $patentReportPath -Raw | ConvertFrom-Json
        if ($patentReport.status -ne "PATENT_MECHANISM_VARIANT_BENCHMARK_READY" -or
            $patentReport.correctness.forward_no_false_prune -ne $true -or
            $patentReport.correctness.bidirectional_no_false_prune -ne $true -or
            [double]$patentReport.incremental_propagation.exact_match_rate -ne 1.0) {
            throw "Patent mechanism benchmark failed its no-false-prune or incremental-equivalence assertions."
        }
        Add-StageResult "patent_mechanism_assertions" "passed" "Finite-action benchmark reports zero false prunes for forward/bidirectional screens and exact incremental/full propagation agreement."

        Write-Host "[BENCHMARK] Validating counterfactual screening report..." -ForegroundColor Yellow
        $counterfactualReportPath = Join-Path $repoRoot "benchmarks\counterfactual_screening_benchmark.json"
        if (-not (Test-Path $counterfactualReportPath)) { throw "Expected counterfactual screening report was not written: $counterfactualReportPath" }
        $counterfactualReport = Get-Content $counterfactualReportPath -Raw | ConvertFrom-Json
        if ($counterfactualReport.all_reference_feasible_actions_retained -ne $true) {
            throw "Counterfactual screening benchmark masked at least one reference-feasible action."
        }
        Add-StageResult "counterfactual_screening_assertions" "passed" "All reference-feasible synthetic actions were retained by the conservative screen."

        Write-Host "[PREFLIGHT] Saving JSON readiness snapshot..." -ForegroundColor Yellow
        & $python scripts/finai_preflight.py --json | Set-Content -Path $preflightPath -Encoding UTF8
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $preflightPath)) { throw "Could not write the preflight JSON snapshot." }
        $preflight = Get-Content $preflightPath -Raw | ConvertFrom-Json
        Add-StageResult "offline_preflight_snapshot" "passed" "Saved package/artifact/provider inventory; absent external assets are recorded rather than claimed ready."

        Write-Host "[LOCAL MODEL] Running loopback-only Colibrì inference smoke (skips when unconfigured)..." -ForegroundColor Yellow
        $localSmokeLines = & $python scripts/smoke_local_colibri.py --timeout-seconds 120 2>&1
        $localSmokeExit = $LASTEXITCODE
        $localSmokeText = @($localSmokeLines) -join [Environment]::NewLine
        if ($localSmokeExit -ne 0) {
            throw "Local Colibrì inference smoke failed with exit code $localSmokeExit. Safe output: $localSmokeText"
        }
        try { $localSmoke = $localSmokeText | ConvertFrom-Json }
        catch { throw "Local Colibrì smoke did not emit valid JSON. Output: $localSmokeText" }
        if ($localSmoke.status -eq "passed") {
            if ($localSmoke.cloud_fallback_used -ne $false -or $localSmoke.network_target -ne "loopback_only") {
                throw "Local Colibrì smoke did not confirm loopback-only operation without cloud fallback."
            }
            Add-StageResult "local_colibri_inference" "passed" "Real local generation succeeded; latency=$($localSmoke.latency_ms)ms, response_chars=$($localSmoke.response_characters), no cloud fallback; generated text was not logged."
        } elseif ($localSmoke.status -eq "skipped_unconfigured") {
            Add-StageResult "local_colibri_inference" "skipped" "No local Colibrì endpoint configured; no model request was made."
        } else {
            throw "Local Colibrì smoke returned unexpected status '$($localSmoke.status)'."
        }


        $report = [ordered]@{
            schema_version = "1.0"
            status = "passed"
            branch = $branchName
            commit = $head
            started_at_utc = $startedAt
            finished_at_utc = [DateTime]::UtcNow.ToString("o")
            verification_scope = "local_backend_frontend_api_paper_ledger_and_synthetic_benchmarks"
            live_execution_enabled = $false
            broker_connected = $false
            live_provider_smoke_opted_in = [bool]($liveProviderSmoke -in @("1", "true", "yes", "on"))
            live_provider_calls_made = $(if ($liveProviderSmoke -in @("1", "true", "yes", "on")) { $null } else { $false })
            stages = @($stageResults)
            benchmark = @{ name = $swarmReport.benchmark; cases = [int]$swarmReport.cases; passed_cases = [int]$swarmReport.passed_cases; failure_count = [int]$swarmReport.failure_count; guardrail_violations = [int]$swarmReport.guardrail_violations }
            patent_mechanism_benchmark = @{
                status = [string]$patentReport.status
                forward_no_false_prune = [bool]$patentReport.correctness.forward_no_false_prune
                bidirectional_no_false_prune = [bool]$patentReport.correctness.bidirectional_no_false_prune
                incremental_exact_match_rate = [double]$patentReport.incremental_propagation.exact_match_rate
                report_file = $patentReportPath
            }
            counterfactual_screening_benchmark = @{
                all_reference_feasible_actions_retained = [bool]$counterfactualReport.all_reference_feasible_actions_retained
                report_file = $counterfactualReportPath
            }
            preflight = @{
                configured_provider_names = @($preflight.provider_credentials.configured_provider_names)
                router_model_present = [bool]$preflight.artifacts.router_model_present
                rag_assets_ready = [bool]$preflight.artifacts.rag_assets_ready
                missing_rag_source_chunks = @($preflight.artifacts.rag_source_chunks_missing)
                missing_rag_assets = @($preflight.artifacts.rag_assets_missing)
                local_model_endpoint_configured = [bool]$preflight.local_inference.colibri_configured
                runtime_reachability_verified_by_preflight = $false
            }
            output_directory = $runDir
            logs = @{ api_stdout = $stdoutPath; api_stderr = $stderrPath; frontend_stdout = $frontendStdoutPath; frontend_stderr = $frontendStderrPath }
            scope_limitations = @(
                "Synthetic safety cases do not demonstrate profitability, forecasting skill, or live-market execution quality.",
                $(if ($liveProviderSmoke -in @("1", "true", "yes", "on")) { "Live provider smoke was explicitly opted in; inspect per-provider smoke output for actual attempted requests and results." } else { "Provider credentials are listed by provider name only; this run does not send paid live LLM prompts." }),
                "Local Colibri model weights/server, licensed RAG corpora, provider reachability, and browser interactions need environment-specific verification.",
                "No live broker adapter, live order submission, live fill reconciliation, or production deployment approval is asserted."
            )
        }
        $report | ConvertTo-Json -Depth 10 | Set-Content -Path $summaryPath -Encoding UTF8
        Add-StageResult "summary_report_written" "passed" $summaryPath
        $report.stages = @($stageResults)
        $report.finished_at_utc = [DateTime]::UtcNow.ToString("o")
        $report | ConvertTo-Json -Depth 10 | Set-Content -Path $summaryPath -Encoding UTF8
        Write-Host ""
        Write-Host "ALL LOCAL ACCEPTANCE CHECKS PASSED" -ForegroundColor Green
        Write-Host "Report: $summaryPath" -ForegroundColor Green
        Write-Host "API stderr: $stderrPath" -ForegroundColor DarkGray
    } finally { Pop-Location }
} catch {
    $failureMessage = $_.Exception.Message
    $failureReport = [ordered]@{ schema_version = "1.0"; status = "failed"; started_at_utc = $startedAt; finished_at_utc = [DateTime]::UtcNow.ToString("o"); failure = $failureMessage; stages = @($stageResults); output_directory = $runDir; logs = @{ api_stdout = $stdoutPath; api_stderr = $stderrPath; frontend_stdout = $frontendStdoutPath; frontend_stderr = $frontendStderrPath } }
    try { $failureReport | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryPath -Encoding UTF8 } catch {}
    Write-Host ""
    Write-Host "FINAI LOCAL ACCEPTANCE CHECKS FAILED: $failureMessage" -ForegroundColor Red
    Write-Host "Report/log directory: $runDir" -ForegroundColor Yellow
    if (Test-Path $stderrPath) { Write-Host "--- API stderr (last 80 lines) ---" -ForegroundColor DarkYellow; Get-Content $stderrPath -Tail 80 }
    throw
} finally {
    foreach ($process in @($frontendProcess, $apiProcess)) {
        if ($null -ne $process) {
            try {
                $process.Refresh()
                if (-not $process.HasExited) {
                    & taskkill.exe /PID $process.Id /T /F 2>$null | Out-Null
                    if ($LASTEXITCODE -ne 0) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
                }
            } catch {}
        }
    }
    Remove-Item -LiteralPath $haltFilePath -Force -ErrorAction SilentlyContinue
    foreach ($name in $environmentNames) { [Environment]::SetEnvironmentVariable($name, $originalEnvironment[$name], "Process") }
}
