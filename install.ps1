# IntelliEye Installer
# Made by Hyunho Cho
# Usage: iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content

Write-Host ""
Write-Host "========================================"
Write-Host "  IntelliEye Installer - Made by Hyunho Cho"
Write-Host "========================================"
Write-Host ""

# ── 1. Python 버전 확인 (3.10~3.12 권장, 3.13 경고, 3.14+ 차단) ──────────────
$pythonCmd = $null
$pyMajor   = 0
$pyMinor   = 0
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $pyMajor = [int]$Matches[1]
            $pyMinor = [int]$Matches[2]
            if ($pyMajor -eq 3 -and $pyMinor -ge 10) {
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
    Write-Host "  1. https://www.python.org/downloads/release/python-3121/ 에서 Python 3.12 다운로드"
    Write-Host "  2. 설치 시 'Add Python to PATH' 옵션을 반드시 체크하세요"
    Write-Host "  3. 설치 완료 후 PowerShell을 재시작하고 다시 실행하세요"
    Write-Host ""
    exit 1
}

# Python 3.14+ 차단: PyTorch 사전 빌드 패키지 미지원
if ($pyMajor -eq 3 -and $pyMinor -ge 14) {
    Write-Host "[오류] Python 3.$pyMinor 는 지원되지 않습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "  PyTorch(torch)는 현재 Python 3.14 이상에 대한 사전 빌드 패키지를" -ForegroundColor Red
    Write-Host "  제공하지 않습니다. torch 설치 단계에서 수십 분 이상 멈추거나 실패합니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "  해결 방법:" -ForegroundColor Cyan
    Write-Host "    1. Python 3.12 를 별도 설치하세요:" -ForegroundColor Cyan
    Write-Host "       https://www.python.org/downloads/release/python-3121/" -ForegroundColor Cyan
    Write-Host "    2. 설치 후 'Add Python to PATH'를 체크하거나, py 런처로 실행하세요:" -ForegroundColor Cyan
    Write-Host "       py -3.12 -m pip install torch ..." -ForegroundColor Cyan
    Write-Host "    3. PowerShell을 재시작하고 인스톨러를 다시 실행하세요." -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# Python 3.13 경고: 호환성 불완전
if ($pyMajor -eq 3 -and $pyMinor -eq 13) {
    Write-Host "[경고] Python 3.$pyMinor 이 감지되었습니다." -ForegroundColor Yellow
    Write-Host "  IntelliEye는 Python 3.10~3.12 환경을 권장합니다." -ForegroundColor Yellow
    Write-Host "  Python 3.13에서는 torch 설치가 오래 걸리거나 실패할 수 있습니다." -ForegroundColor Yellow
    Write-Host ""
    $confirm = Read-Host "  계속 진행하시겠습니까? (Y 계속 / 그 외 종료)"
    if ($confirm -notmatch "^[Yy]") {
        Write-Host ""
        Write-Host "  Python 3.12 권장 다운로드: https://www.python.org/downloads/release/python-3121/" -ForegroundColor Cyan
        Write-Host ""
        exit 0
    }
    Write-Host ""
}

Write-Host "[OK] Python 확인: $($ver)" -ForegroundColor Green

# ── HF_HUB_DISABLE_SYMLINKS_WARNING 환경변수 설정 ─────────────────────────────
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
[System.Environment]::SetEnvironmentVariable("HF_HUB_DISABLE_SYMLINKS_WARNING", "1", "User")

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

# pip 최신 버전으로 업그레이드
Write-Host "  pip 업그레이드 중..."
& $pythonCmd -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [경고] pip 업그레이드에 실패했습니다. 설치를 계속하지만 호환성 문제가 발생할 수 있습니다." -ForegroundColor Yellow
    Write-Host "  수동 업그레이드: $pythonCmd -m pip install --upgrade pip" -ForegroundColor Yellow
}

# torch + torchvision + torchaudio 먼저 설치 (CPU 버전)
Write-Host ""
Write-Host "  torch / torchvision / torchaudio 설치 중..." -ForegroundColor Cyan
Write-Host "  (CPU 전용 패키지 다운로드 — 약 500MB~1GB, 인터넷 속도에 따라 5~20분 소요)" -ForegroundColor DarkGray
Write-Host "  (설치 중 화면이 멈춘 것처럼 보여도 정상입니다. 기다려 주세요...)" -ForegroundColor DarkGray
$torchStart = Get-Date
& $pythonCmd -m pip install `
    torch torchvision torchaudio `
    --index-url https://download.pytorch.org/whl/cpu `
    --no-cache-dir `
    --timeout 120
$torchElapsed = [math]::Round(((Get-Date) - $torchStart).TotalSeconds)
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[오류] torch 설치에 실패했습니다. ($torchElapsed 초 경과)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  가능한 원인:" -ForegroundColor Yellow
    Write-Host "    - Python 3.$pyMinor 에 맞는 torch wheel이 없습니다." -ForegroundColor Yellow
    Write-Host "    - 네트워크 연결 또는 방화벽/프록시 환경을 확인하세요." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  해결 방법:" -ForegroundColor Cyan
    Write-Host "    1. Python 3.12 를 설치하고 다시 실행하세요:" -ForegroundColor Cyan
    Write-Host "       https://www.python.org/downloads/release/python-3121/" -ForegroundColor Cyan
    Write-Host "    2. 또는 아래 명령으로 torch만 수동 설치를 시도하세요:" -ForegroundColor Cyan
    Write-Host "       pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
Write-Host "  [OK] torch 설치 완료 ($torchElapsed 초 소요)" -ForegroundColor Green

$reqFile = Join-Path $installDir "requirements.txt"
Write-Host ""
Write-Host "  나머지 패키지 설치 중..."
& $pythonCmd -m pip install -r $reqFile --no-cache-dir --timeout 120
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

# ── 6. PowerShell Profile에 intellieye 함수 등록 ──────────────────────────────
$profileContent = @"

# IntelliEye Agent
function intellieye {
    param([string]`$Command)
    `$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not `$pythonPath) { Write-Host "Python을 찾을 수 없습니다." -ForegroundColor Red; return }
    if (`$Command -eq "update") {
        & `$pythonPath "$HOME\intellieye\intellieye.py" --update
    } else {
        & `$pythonPath "$HOME\intellieye\intellieye.py" `$Command
    }
}
"@

# Profile 파일이 없으면 생성
if (-not (Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force | Out-Null
}

# 중복 추가 방지
if (-not (Select-String -Path $PROFILE -Pattern "IntelliEye Agent" -Quiet)) {
    Add-Content -Path $PROFILE -Value $profileContent
}

Write-Host "[OK] 'intellieye' 명령어가 PowerShell Profile에 등록되었습니다!" -ForegroundColor Green

# ── 7. 완료 메시지 ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================"
Write-Host "  ✅ IntelliEye 설치 완료!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "사용법:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  intellieye          → 에이전트 시작" -ForegroundColor Yellow
Write-Host "  intellieye update   → 최신 버전으로 업데이트" -ForegroundColor Yellow
Write-Host ""
Write-Host "※ 새 PowerShell 창을 열어야 명령어가 활성화됩니다." -ForegroundColor Cyan
Write-Host ""
