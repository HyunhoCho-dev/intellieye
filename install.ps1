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
                if ($major -eq 3 -and $minor -ge 14) {
                    Write-Host "[경고] Python $major.$minor 이 감지되었습니다." -ForegroundColor Yellow
                    Write-Host "  IntelliEye는 Python 3.10~3.12 환경을 권장합니다." -ForegroundColor Yellow
                    Write-Host "  일부 패키지가 정상적으로 설치되지 않을 수 있습니다." -ForegroundColor Yellow
                    Write-Host ""
                }
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

# torch + torchvision + torchaudio 먼저 설치 (CPU 버전)
Write-Host "  torch / torchvision / torchaudio 설치 중..."
& $pythonCmd -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) {
    Write-Host "[오류] torch 설치에 실패했습니다." -ForegroundColor Red
    exit 1
}

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
