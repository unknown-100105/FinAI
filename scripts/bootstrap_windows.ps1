[CmdletBinding()]
param(
    [switch]$InstallCalibre
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Executable $($Arguments -join ' ')"
    }
}

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating project virtual environment at .venv ..."
    Invoke-Checked -Executable "python" -Arguments @("-m", "venv", ".venv")
}
if (-not (Test-Path $VenvPython)) {
    throw "Could not find .venv\Scripts\python.exe after creating the environment."
}

Write-Host "Installing FinAI runtime and test dependencies ..."
Invoke-Checked -Executable $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
Invoke-Checked -Executable $VenvPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt")

Write-Host "Checking interpreter and core imports ..."
Invoke-Checked -Executable $VenvPython -Arguments @(
    "-c",
    "import importlib.util, sys; names=['fastapi','pydantic','requests','numpy','pandas','sklearn','joblib','faiss','torch','pytest','yfinance']; missing=[n for n in names if importlib.util.find_spec(n) is None]; print('Python:', sys.executable); print('Missing imports:', missing); raise SystemExit(1 if missing else 0)"
)

Write-Host ""
Write-Host "Backend dependencies installed in .venv."
Write-Host "Run tests with the environment's interpreter:"
Write-Host "  .\.venv\Scripts\python.exe -m pytest -q"
Write-Host "Or activate it in this PowerShell terminal:"
Write-Host "  .\.venv\Scripts\Activate.ps1"

if ($InstallCalibre) {
    $CalibrePython = Join-Path $RepoRoot ".venv-calibre\Scripts\python.exe"
    Write-Host ""
    Write-Host "Calibre requires Python 3.12+. Creating a separate .venv-calibre ..."
    Invoke-Checked -Executable "py" -Arguments @("-3.12", "-m", "venv", ".venv-calibre")
    if (-not (Test-Path $CalibrePython)) {
        throw "Python 3.12 was not found. Install Python 3.12, then rerun with -InstallCalibre."
    }
    Invoke-Checked -Executable $CalibrePython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-Checked -Executable $CalibrePython -Arguments @("-m", "pip", "install", "-r", "requirements-calibre.txt")
    Invoke-Checked -Executable $CalibrePython -Arguments @(
        "-c",
        "import sys, calibre; print('Calibre interpreter:', sys.executable); print('Calibre package:', calibre.__file__)"
    )
    Write-Host "Calibre environment is separate; use .\.venv-calibre\Scripts\python.exe for Calibre-specific experiments."
}
