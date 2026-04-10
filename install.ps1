# IntelliEye Installer
# Made by Hyunho Cho
# Usage: iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content

Write-Host ""
Write-Host "========================================"
Write-Host "  IntelliEye Installer - Made by Hyunho Cho"
Write-Host "========================================"
Write-Host ""

# ── 1. Locate Python 3.12 → auto-install via winget if not found ─────────────

# Helper: check whether a specific minor version is available via the py launcher
function Test-PyVersion {
    param([string]$Minor)
    try {
        $out = & py "-3.$Minor" --version 2>&1
        return ($out -match "Python 3\.$Minor")
    } catch { return $false }
}

# Return the Python 3.12 executable path, or $null if not found
function Find-Python312 {
    # Prefer the py launcher
    if (Test-PyVersion "12") { return "py -3.12" }

    # Fall back to direct PATH search
    foreach ($candidate in @("python3.12", "python312", "python")) {
        try {
            $out = & $candidate --version 2>&1
            if ($out -match "Python 3\.12") { return $candidate }
        } catch { }
    }
    return $null
}

Write-Host "Searching for Python 3.12..." -ForegroundColor Cyan
$py312 = Find-Python312

if (-not $py312) {
    # Detect the default Python version for informational purposes
    $defaultVer = ""
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $out = & $cmd --version 2>&1
            if ($out -match "Python (\d+\.\d+)") { $defaultVer = $Matches[0]; break }
        } catch { }
    }

    Write-Host ""
    if ($defaultVer) {
        Write-Host "  System Python detected: $defaultVer" -ForegroundColor Yellow
    }
    Write-Host "  Python 3.12 was not found." -ForegroundColor Yellow
    Write-Host ""

    # Attempt automatic installation via winget
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "  Installing Python 3.12 automatically via winget..." -ForegroundColor Cyan
        Write-Host "  (A UAC prompt may appear — click 'Yes' to continue.)" -ForegroundColor DarkGray
        Write-Host ""
        winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "  [WARNING] winget installation failed or was cancelled." -ForegroundColor Yellow
        } else {
            Write-Host ""
            Write-Host "  [OK] Python 3.12 installed. Refreshing PATH..." -ForegroundColor Green
            # Refresh PATH in the current session
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")
        }

        # Re-search after installation
        $py312 = Find-Python312
    }

    if (-not $py312) {
        Write-Host ""
        Write-Host "[ERROR] Could not find or auto-install Python 3.12." -ForegroundColor Red
        Write-Host ""
        Write-Host "  Manual installation:" -ForegroundColor Cyan
        Write-Host "    1. Download Python 3.12 from https://www.python.org/downloads/release/python-3121/" -ForegroundColor Cyan
        Write-Host "    2. Check 'Add Python to PATH' or the py launcher option during install." -ForegroundColor Cyan
        Write-Host "    3. Restart PowerShell and run the installer again." -ForegroundColor Cyan
        Write-Host ""
        if ($defaultVer -match "Python 3\.1[4-9]") {
            Write-Host "  NOTE: $defaultVer is not compatible with PyTorch (torch) — installation will fail." -ForegroundColor Red
            Write-Host "    You must use Python 3.12." -ForegroundColor Red
            Write-Host ""
        }
        exit 1
    }
}

# Split "py -3.12" into executable + args if needed
if ($py312 -eq "py -3.12") {
    $pyExe  = "py"
    $pyArgs = @("-3.12")
} else {
    $pyExe  = $py312
    $pyArgs = @()
}

# Print confirmed Python version
$verOut = & $pyExe @pyArgs --version 2>&1
Write-Host "[OK] Python 3.12 confirmed: $verOut" -ForegroundColor Green

# ── Set HF_HUB_DISABLE_SYMLINKS_WARNING ──────────────────────────────────────
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
[System.Environment]::SetEnvironmentVariable("HF_HUB_DISABLE_SYMLINKS_WARNING", "1", "User")

# ── 2. Create installation directory ─────────────────────────────────────────
$installDir = Join-Path $HOME "intellieye"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}
Write-Host "[OK] Install directory: $installDir" -ForegroundColor Green

# ── 2a. Create virtual environment (venv) ────────────────────────────────────
$venvDir = Join-Path $installDir ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Host ""
    Write-Host "Creating Python 3.12 virtual environment..." -ForegroundColor Cyan
    & $pyExe @pyArgs -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Virtual environment created: $venvDir" -ForegroundColor Green
} else {
    Write-Host "[OK] Reusing existing virtual environment: $venvDir" -ForegroundColor Green
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip    = Join-Path $venvDir "Scripts\pip.exe"

# ── 3. Download source files ──────────────────────────────────────────────────
$baseUrl = "https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main"
$files   = @(
    "intellieye.py",
    "screen_capture.py",
    "model.py",
    "controller.py",
    "requirements.txt"
)

Write-Host ""
Write-Host "Downloading source files..." -ForegroundColor Cyan
foreach ($file in $files) {
    $url  = "$baseUrl/$file"
    $dest = Join-Path $installDir $file
    Write-Host "  Downloading: $file"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    } catch {
        Write-Host "  [ERROR] Failed to download $file : $_" -ForegroundColor Red
        exit 1
    }
}
Write-Host "[OK] Source files downloaded" -ForegroundColor Green

# ── 4. Install packages (inside venv) ────────────────────────────────────────
Write-Host ""
Write-Host "Installing packages (this may take a while)..." -ForegroundColor Cyan

# Upgrade pip / setuptools / wheel first
Write-Host "  Upgrading pip / setuptools / wheel..."
& $venvPython -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARNING] pip upgrade failed. Continuing anyway." -ForegroundColor Yellow
}

# Install torch + torchvision + torchaudio first (CPU build)
Write-Host ""
Write-Host "  Installing torch / torchvision / torchaudio (CPU build)..." -ForegroundColor Cyan
Write-Host "  ~500 MB-1 GB download — expect 5-20 minutes depending on your connection." -ForegroundColor DarkGray
Write-Host "  Progress will appear below in real time." -ForegroundColor DarkGray
Write-Host ""
$torchStart = Get-Date
& $venvPython -m pip install `
    torch torchvision torchaudio `
    --index-url https://download.pytorch.org/whl/cpu `
    --no-cache-dir `
    --timeout 300 `
    --progress-bar on
$torchElapsed = [math]::Round(((Get-Date) - $torchStart).TotalSeconds)
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] torch installation failed. ($torchElapsed seconds elapsed)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Possible causes:" -ForegroundColor Yellow
    Write-Host "    - Check your network connection or firewall/proxy settings." -ForegroundColor Yellow
    Write-Host "    - The PyTorch server may be temporarily slow. Try again later." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  To install torch manually:" -ForegroundColor Cyan
    Write-Host "    $venvPip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
Write-Host ""
Write-Host "  [OK] torch installed ($torchElapsed seconds)" -ForegroundColor Green

$reqFile = Join-Path $installDir "requirements.txt"
Write-Host ""
Write-Host "  Installing remaining packages..."
& $venvPython -m pip install -r $reqFile --no-cache-dir --timeout 120
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Package installation failed." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] All packages installed" -ForegroundColor Green

# ── 5. Create launcher script ─────────────────────────────────────────────────
$runScript = Join-Path $installDir "run.ps1"
$mainPy    = Join-Path $installDir "intellieye.py"
# Use the venv Python directly so PATH is not required
Set-Content -Path $runScript -Value "& `"$venvPython`" `"$mainPy`""
Write-Host "[OK] Launcher created: $runScript" -ForegroundColor Green

# ── 6. Register 'intellieye' function in PowerShell Profile ──────────────────
$profileContent = @"

# IntelliEye Agent
function intellieye {
    param([string]`$Command)
    `$venvPy = "$venvPython"
    if (-not (Test-Path `$venvPy)) { Write-Host "IntelliEye virtual environment not found. Please re-run the installer." -ForegroundColor Red; return }
    if (`$Command -eq "update") {
        & `$venvPy "$mainPy" --update
    } else {
        & `$venvPy "$mainPy" `$Command
    }
}
"@

# Create profile file if it doesn't exist
if (-not (Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force | Out-Null
}

# Avoid duplicate entries
if (-not (Select-String -Path $PROFILE -Pattern "IntelliEye Agent" -Quiet)) {
    Add-Content -Path $PROFILE -Value $profileContent
}

Write-Host "[OK] 'intellieye' command registered in PowerShell Profile!" -ForegroundColor Green

# ── 7. Done ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================"
Write-Host "  ✅ IntelliEye installation complete!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  intellieye          → start the agent" -ForegroundColor Yellow
Write-Host "  intellieye update   → update to the latest version" -ForegroundColor Yellow
Write-Host ""
Write-Host "Or run directly:" -ForegroundColor Cyan
Write-Host "  powershell `"$runScript`"" -ForegroundColor Yellow
Write-Host ""
Write-Host "NOTE: Open a new PowerShell window to activate the 'intellieye' command." -ForegroundColor Cyan
Write-Host ""
