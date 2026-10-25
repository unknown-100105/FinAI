#requires -Version 5.1
<#
.SYNOPSIS
Starts the FinAI FastAPI backend and Vite frontend together for local development.
.DESCRIPTION
Binds both services to loopback, keeps live trading disabled, and leaves the
paper ledger disabled unless -EnablePaperLedger is explicitly supplied.
Press Ctrl+C to stop both child processes.
#>
[CmdletBinding()]
param(
    [switch]$EnablePaperLedger
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }
$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($null -eq $npmCommand) { $npmCommand = Get-Command npm -ErrorAction SilentlyContinue }
if ($null -eq $npmCommand) { throw "npm was not found on PATH. Install Node.js LTS and reopen PowerShell." }
$npm = $npmCommand.Source
$apiPort = 8000
$frontendPort = 5173
$timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss-fff")
$logDir = Join-Path $repoRoot "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$apiLog = Join-Path $logDir "finai-dev-api-$timestamp.log"
$frontendLog = Join-Path $logDir "finai-dev-frontend-$timestamp.log"
$apiProcess = $null
$frontendProcess = $null
$envNames = @("FINAI_LIVE_TRADING_ENABLED", "FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "FINAI_SWARMTRADE_PAPER_DB")
$oldEnv = @{}
foreach ($name in $envNames) { $oldEnv[$name] = [Environment]::GetEnvironmentVariable($name, "Process") }

function Assert-LocalPortFree {
    param([int]$Port)
    $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start() }
    catch { throw "Port $Port is already in use. Stop the service using 127.0.0.1:$Port and retry." }
    finally { if ($null -ne $listener) { $listener.Stop() } }
}

try {
    Assert-LocalPortFree -Port $apiPort
    Assert-LocalPortFree -Port $frontendPort
    [Environment]::SetEnvironmentVariable("FINAI_LIVE_TRADING_ENABLED", "0", "Process")

    if ($EnablePaperLedger) {
        $paperDir = Join-Path $repoRoot "data\swarmtrade"
        New-Item -ItemType Directory -Path $paperDir -Force | Out-Null
        [Environment]::SetEnvironmentVariable("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1", "Process")
        [Environment]::SetEnvironmentVariable("FINAI_SWARMTRADE_PAPER_DB", (Join-Path $paperDir "paper_ledger.dev.sqlite3"), "Process")
        Write-Host "Paper ledger: ENABLED (simulation only; no live orders)" -ForegroundColor Yellow
    } else {
        [Environment]::SetEnvironmentVariable("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", $null, "Process")
        [Environment]::SetEnvironmentVariable("FINAI_SWARMTRADE_PAPER_DB", $null, "Process")
        Write-Host "Paper ledger: disabled (pass -EnablePaperLedger to opt in)" -ForegroundColor DarkYellow
    }

    Push-Location $repoRoot
    try {
        Write-Host "Starting FinAI API on http://127.0.0.1:$apiPort ..." -ForegroundColor Cyan
        $apiProcess = Start-Process -FilePath $python -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port $apiPort" -WorkingDirectory $repoRoot -PassThru -NoNewWindow -RedirectStandardOutput $apiLog -RedirectStandardError $apiLog

        $apiHealthy = $false
        for ($attempt = 0; $attempt -lt 45; $attempt++) {
            $apiProcess.Refresh()
            if ($apiProcess.HasExited) { throw "FinAI API exited during startup. Inspect $apiLog" }
            try {
                $health = Invoke-RestMethod -Uri "http://127.0.0.1:$apiPort/health" -Method Get -TimeoutSec 2
                if ($health.status -eq "ok") { $apiHealthy = $true; break }
            } catch { Start-Sleep -Seconds 1 }
        }
        if (-not $apiHealthy) { throw "FinAI API did not become healthy within 45 seconds. Inspect $apiLog" }

        Write-Host "Starting Vite frontend on http://127.0.0.1:$frontendPort ..." -ForegroundColor Cyan
        $frontendProcess = Start-Process -FilePath $npm -ArgumentList "run dev -- --host 127.0.0.1 --port $frontendPort --strictPort" -WorkingDirectory $frontendRoot -PassThru -NoNewWindow -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendLog

        Start-Sleep -Seconds 3
        $frontendProcess.Refresh()
        if ($frontendProcess.HasExited) { throw "Vite frontend exited during startup. Inspect $frontendLog" }

        Write-Host ""
        Write-Host "FinAI development services started." -ForegroundColor Green
        Write-Host "API:       http://127.0.0.1:$apiPort"
        Write-Host "Swagger:   http://127.0.0.1:$apiPort/docs"
        Write-Host "Frontend:  http://127.0.0.1:$frontendPort"
        Write-Host "API log:   $apiLog"
        Write-Host "UI log:    $frontendLog"
        Write-Host "Press Ctrl+C to stop both services." -ForegroundColor Yellow

        while ($true) {
            Start-Sleep -Seconds 2
            $apiProcess.Refresh()
            $frontendProcess.Refresh()
            if ($apiProcess.HasExited) { throw "FinAI API process exited. Inspect $apiLog" }
            if ($frontendProcess.HasExited) { throw "Vite frontend process exited. Inspect $frontendLog" }
        }
    }
    finally { Pop-Location }
}
catch {
    Write-Host "FinAI development launcher stopped: $($_.Exception.Message)" -ForegroundColor Red
    throw
}
finally {
    foreach ($process in @($frontendProcess, $apiProcess)) {
        if ($null -ne $process) {
            try { $process.Refresh(); if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue } } catch {}
        }
    }
    foreach ($name in $envNames) { [Environment]::SetEnvironmentVariable($name, $oldEnv[$name], "Process") }
}
