[CmdletBinding()]
param(
    [switch]$SkipApi,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$frontendRoot = Join-Path $repoRoot "frontend"
$frontendPackage = Join-Path $frontendRoot "package.json"

function Get-ListeningPids {
    param([int]$Port)
    try {
        return @(
            Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop |
                Select-Object -ExpandProperty OwningProcess -Unique
        )
    } catch {
        return @()
    }
}

function Start-PowerShellWindow {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptText
    )
    $encoded = [Convert]::ToBase64String(
        [System.Text.Encoding]::Unicode.GetBytes($ScriptText)
    )
    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $encoded
    ) | Out-Null
}

if (-not $SkipApi) {
    if (-not (Test-Path $pythonPath)) {
        throw "FinAI Python environment not found at $pythonPath. Create .venv and install requirements first."
    }

    $apiPids = Get-ListeningPids -Port 8000
    if ($apiPids.Count -gt 0) {
        Write-Warning "Port 8000 is already listening (PID: $($apiPids -join ', ')). I will not terminate or replace that process. Check /health and /api/v1/models; stop a stale server manually before rerunning."
    } else {
        $backendScript = @'
Set-Location "__REPO__"
$env:FINAI_ENV = "development"
$env:FINAI_API_AUTH_MODE = "development"
$env:FINAI_IDENTITY_MODE = "demo"
$env:FINAI_DEMO_AUTH = "true"
Write-Host "FinAI backend: http://127.0.0.1:8000"
Write-Host "Development/demo settings are scoped to this process."
& "__PYTHON__" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
'@
        $backendScript = $backendScript.Replace("__REPO__", $repoRoot).Replace("__PYTHON__", $pythonPath)
        Start-PowerShellWindow -ScriptText $backendScript
        Write-Host "Started a backend terminal on 127.0.0.1:8000."
    }
}

if (-not $SkipFrontend) {
    if (-not (Test-Path $frontendPackage)) {
        throw "Frontend package.json not found at $frontendPackage."
    }

    if (-not (Test-Path (Join-Path $frontendRoot "node_modules"))) {
        Write-Warning "Frontend dependencies are missing. Run npm ci in the frontend directory first."
    }

    $frontendPids = Get-ListeningPids -Port 5173
    if ($frontendPids.Count -gt 0) {
        Write-Warning "Port 5173 is already listening (PID: $($frontendPids -join ', ')); I will not replace that process."
    } else {
        $frontendScript = @'
Set-Location "__FRONTEND__"
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
Write-Host "FinAI frontend will use API http://127.0.0.1:8000"
npm run dev -- --host 127.0.0.1 --port 5173
'@
        $frontendScript = $frontendScript.Replace("__FRONTEND__", $frontendRoot)
        Start-PowerShellWindow -ScriptText $frontendScript
        Write-Host "Started a frontend terminal on 127.0.0.1:5173."
    }
}

Write-Host ""
Write-Host "Open frontend:   http://127.0.0.1:5173"
Write-Host "Backend health:  http://127.0.0.1:8000/health"
Write-Host "Model registry:  http://127.0.0.1:8000/api/v1/models"
Write-Host "Causal graph:    http://127.0.0.1:8000/api/v1/causal-risk/graph"
Write-Host ""
Write-Host "This helper is for loopback development only; do not expose the development server publicly."
