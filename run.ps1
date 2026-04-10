# IntelliEye Launcher
# Made by Hyunho Cho
# Usage: powershell "$HOME\intellieye\run.ps1"
#
# This script starts IntelliEye using the Python 3.12 virtual environment that
# was created by install.ps1. If the virtual environment is missing or does not
# use Python 3.12, a clear error message is shown with actionable guidance.

$installDir = Join-Path $HOME "intellieye"
$venvDir    = Join-Path $installDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$mainPy     = Join-Path $installDir "intellieye.py"

Write-Host ""
Write-Host "========================================"
Write-Host "  IntelliEye - AI Screen Control Agent"
Write-Host "  Made by Hyunho Cho"
Write-Host "========================================"
Write-Host ""

# ── 1. Verify that the virtual environment exists ────────────────────────────
if (-not (Test-Path $venvPython)) {
    Write-Host "[ERROR] Virtual environment not found at: $venvDir" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please run the installer first:" -ForegroundColor Cyan
    Write-Host "    iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# ── 2. Confirm the venv Python is version 3.12 ───────────────────────────────
$pyVerOut = & $venvPython --version 2>&1
if ($pyVerOut -notmatch "Python 3\.12") {
    Write-Host "[WARNING] Virtual environment Python is not 3.12: $pyVerOut" -ForegroundColor Yellow
    Write-Host "  IntelliEye requires Python 3.12 for full compatibility with PyTorch." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  To fix, remove the old virtual environment and re-run the installer:" -ForegroundColor Cyan
    Write-Host "    Remove-Item -Recurse -Force `"$venvDir`"" -ForegroundColor Yellow
    Write-Host "    iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content" -ForegroundColor Yellow
    Write-Host ""
    $cont = Read-Host "Continue anyway? (y/N)"
    if ($cont -notmatch "^[Yy]$") { exit 1 }
}

# ── 3. Verify that the main script exists ────────────────────────────────────
if (-not (Test-Path $mainPy)) {
    Write-Host "[ERROR] intellieye.py not found at: $mainPy" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please re-run the installer to download the latest files:" -ForegroundColor Cyan
    Write-Host "    iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# ── 4. Launch IntelliEye ──────────────────────────────────────────────────────
Write-Host "Starting IntelliEye..." -ForegroundColor Cyan
Write-Host "  Python : $pyVerOut" -ForegroundColor DarkGray
Write-Host "  Script : $mainPy" -ForegroundColor DarkGray
Write-Host ""

& $venvPython $mainPy @args
