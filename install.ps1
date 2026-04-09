# IntelliEye Installer
# Made by Hyunho Cho
# Usage: iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content

Write-Host ""
Write-Host "========================================"
Write-Host "  IntelliEye Installer - Made by Hyunho Cho"
Write-Host "========================================"
Write-Host ""

# ── 1. Python 3.10+ 확인 ──────────────────────────────────────────────────────
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 10)) {
                $pythonCmd = $cmd
                break
            }
        }
    } catch { }
}

if (-not $pythonCmd) {
    Write-Host "[오류] Python 3.10 이상이 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "Python 설치 방법:"
    Write-Host "  1. https://www.python.org/downloads/ 에서 최신 Python 다운로드"
    Write-Host "  2. 설치 시 'Add Python to PATH' 옵션을 반드시 체크하세요"
    Write-Host "  3. 설치 완료 후 PowerShell을 재시작하고 다시 실행하세요"
    Write-Host ""
    exit 1
}

Write-Host "[OK] Python 확인: $($ver)" -ForegroundColor Green

# ── 2. 설치 디렉토리 생성 ─────────────────────────────────────────────────────
$installDir = Join-Path $HOME "intellieye"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}
Write-Host "[OK] 설치 디렉토리: $installDir" -ForegroundColor Green

# ── 3. 소스 파일 다운로드 ─────────────────────────────────────────────────────
$baseUrl = "https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main"
$files   = @(
    "intellieye.py",
    "screen_capture.py",
    "model.py",
    "controller.py",
    "requirements.txt"
)

Write-Host ""
Write-Host "소스 파일을 다운로드합니다..." -ForegroundColor Cyan
foreach ($file in $files) {
    $url  = "$baseUrl/$file"
    $dest = Join-Path $installDir $file
    Write-Host "  다운로드: $file"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    } catch {
        Write-Host "  [오류] $file 다운로드 실패: $_" -ForegroundColor Red
        exit 1
    }
}
Write-Host "[OK] 파일 다운로드 완료" -ForegroundColor Green

# ── 4. pip install ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "패키지를 설치합니다 (시간이 걸릴 수 있습니다)..." -ForegroundColor Cyan
$reqFile = Join-Path $installDir "requirements.txt"
& $pythonCmd -m pip install -r $reqFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "[오류] 패키지 설치에 실패했습니다." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] 패키지 설치 완료" -ForegroundColor Green

# ── 5. 런처 스크립트 생성 ─────────────────────────────────────────────────────
$runScript = Join-Path $installDir "run.ps1"
$mainPy    = Join-Path $installDir "intellieye.py"
Set-Content -Path $runScript -Value "python `"$mainPy`""
Write-Host "[OK] 런처 생성: $runScript" -ForegroundColor Green

# ── 6. 완료 메시지 ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================"
Write-Host "  IntelliEye 설치 완료!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "실행 방법:"
Write-Host ""
Write-Host "  powershell `"$runScript`"" -ForegroundColor Yellow
Write-Host ""
Write-Host "또는 PowerShell에서:"
Write-Host ""
Write-Host "  cd `"$installDir`"" -ForegroundColor Yellow
Write-Host "  python intellieye.py" -ForegroundColor Yellow
Write-Host ""
