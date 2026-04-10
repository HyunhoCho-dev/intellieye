# IntelliEye Installer
# Made by Hyunho Cho
# Usage: iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content

Write-Host ""
Write-Host "========================================"
Write-Host "  IntelliEye Installer - Made by Hyunho Cho"
Write-Host "========================================"
Write-Host ""

# ── 1. Python 3.12 우선 탐색 → 없으면 winget 자동 설치 ───────────────────────

# 헬퍼: py 런처로 특정 버전 실행 가능 여부 확인
function Test-PyVersion {
    param([string]$Minor)
    try {
        $out = & py "-3.$Minor" --version 2>&1
        return ($out -match "Python 3\.$Minor")
    } catch { return $false }
}

# Python 3.12 전용 실행 파일 경로를 반환 (없으면 $null)
function Find-Python312 {
    # py 런처 우선
    if (Test-PyVersion "12") { return "py -3.12" }

    # PATH 직접 탐색
    foreach ($candidate in @("python3.12", "python312", "python")) {
        try {
            $out = & $candidate --version 2>&1
            if ($out -match "Python 3\.12") { return $candidate }
        } catch { }
    }
    return $null
}

Write-Host "Python 3.12 을 탐색합니다..." -ForegroundColor Cyan
$py312 = Find-Python312

if (-not $py312) {
    # 기본 Python 버전 감지 (3.14+ 여부 안내용)
    $defaultVer = ""
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $out = & $cmd --version 2>&1
            if ($out -match "Python (\d+\.\d+)") { $defaultVer = $Matches[0]; break }
        } catch { }
    }

    Write-Host ""
    if ($defaultVer) {
        Write-Host "  현재 시스템 Python: $defaultVer" -ForegroundColor Yellow
    }
    Write-Host "  Python 3.12 가 감지되지 않았습니다." -ForegroundColor Yellow
    Write-Host ""

    # winget 으로 자동 설치 시도
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "  winget 을 사용하여 Python 3.12 를 자동으로 설치합니다..." -ForegroundColor Cyan
        Write-Host "  (UAC 권한 창이 뜰 수 있습니다. '예' 를 클릭하세요.)" -ForegroundColor DarkGray
        Write-Host ""
        winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "  [경고] winget 설치가 실패하거나 취소되었습니다." -ForegroundColor Yellow
        } else {
            Write-Host ""
            Write-Host "  [OK] Python 3.12 설치 완료. PATH 를 갱신합니다..." -ForegroundColor Green
            # 현재 세션 PATH 에 Python 3.12 경로 반영
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")
        }

        # 설치 후 재탐색
        $py312 = Find-Python312
    }

    if (-not $py312) {
        Write-Host ""
        Write-Host "[오류] Python 3.12 를 찾거나 자동 설치할 수 없었습니다." -ForegroundColor Red
        Write-Host ""
        Write-Host "  수동 설치 방법:" -ForegroundColor Cyan
        Write-Host "    1. https://www.python.org/downloads/release/python-3121/ 에서 Python 3.12 다운로드" -ForegroundColor Cyan
        Write-Host "    2. 설치 시 'Add Python to PATH' 또는 py 런처 옵션을 반드시 체크하세요." -ForegroundColor Cyan
        Write-Host "    3. PowerShell 을 재시작한 뒤 인스톨러를 다시 실행하세요." -ForegroundColor Cyan
        Write-Host ""
        if ($defaultVer -match "Python 3\.1[4-9]") {
            Write-Host "  ※ $defaultVer 는 PyTorch(torch) 와 호환되지 않아 설치가 실패합니다." -ForegroundColor Red
            Write-Host "    반드시 Python 3.12 를 사용하세요." -ForegroundColor Red
            Write-Host ""
        }
        exit 1
    }
}

# $py312 가 "py -3.12" 형식이면 분리
if ($py312 -eq "py -3.12") {
    $pyExe  = "py"
    $pyArgs = @("-3.12")
} else {
    $pyExe  = $py312
    $pyArgs = @()
}

# 버전 확인 출력
$verOut = & $pyExe @pyArgs --version 2>&1
Write-Host "[OK] Python 3.12 확인: $verOut" -ForegroundColor Green

# ── HF_HUB_DISABLE_SYMLINKS_WARNING 환경변수 설정 ─────────────────────────────
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
[System.Environment]::SetEnvironmentVariable("HF_HUB_DISABLE_SYMLINKS_WARNING", "1", "User")

# ── 2. 설치 디렉토리 생성 ─────────────────────────────────────────────────────
$installDir = Join-Path $HOME "intellieye"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}
Write-Host "[OK] 설치 디렉토리: $installDir" -ForegroundColor Green

# ── 2a. 가상환경(venv) 생성 ───────────────────────────────────────────────────
$venvDir = Join-Path $installDir ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Host ""
    Write-Host "Python 3.12 가상환경을 생성합니다..." -ForegroundColor Cyan
    & $pyExe @pyArgs -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[오류] 가상환경 생성에 실패했습니다." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] 가상환경 생성 완료: $venvDir" -ForegroundColor Green
} else {
    Write-Host "[OK] 기존 가상환경 재사용: $venvDir" -ForegroundColor Green
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip    = Join-Path $venvDir "Scripts\pip.exe"

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

# ── 4. 패키지 설치 (venv 안에서) ─────────────────────────────────────────────
Write-Host ""
Write-Host "패키지를 설치합니다 (시간이 걸릴 수 있습니다)..." -ForegroundColor Cyan

# pip / setuptools / wheel 업그레이드
Write-Host "  pip / setuptools / wheel 업그레이드 중..."
& $venvPython -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [경고] pip 업그레이드에 실패했습니다. 설치를 계속합니다." -ForegroundColor Yellow
}

# torch + torchvision + torchaudio 먼저 설치 (CPU 버전)
Write-Host ""
Write-Host "  torch / torchvision / torchaudio 설치 중 (CPU 전용)..." -ForegroundColor Cyan
Write-Host "  약 500MB~1GB 다운로드 — 인터넷 속도에 따라 5~20분 소요됩니다." -ForegroundColor DarkGray
Write-Host "  진행 상황이 아래에 실시간으로 출력됩니다." -ForegroundColor DarkGray
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
    Write-Host "[오류] torch 설치에 실패했습니다. ($torchElapsed 초 경과)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  가능한 원인:" -ForegroundColor Yellow
    Write-Host "    - 네트워크 연결 또는 방화벽/프록시 환경을 확인하세요." -ForegroundColor Yellow
    Write-Host "    - PyTorch 서버가 일시적으로 느릴 수 있습니다. 잠시 후 재시도하세요." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  수동으로 torch 만 설치하려면:" -ForegroundColor Cyan
    Write-Host "    $venvPip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
Write-Host ""
Write-Host "  [OK] torch 설치 완료 ($torchElapsed 초 소요)" -ForegroundColor Green

$reqFile = Join-Path $installDir "requirements.txt"
Write-Host ""
Write-Host "  나머지 패키지 설치 중..."
& $venvPython -m pip install -r $reqFile --no-cache-dir --timeout 120
if ($LASTEXITCODE -ne 0) {
    Write-Host "[오류] 패키지 설치에 실패했습니다." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] 패키지 설치 완료" -ForegroundColor Green

# ── 5. 런처 스크립트 생성 ─────────────────────────────────────────────────────
$runScript = Join-Path $installDir "run.ps1"
$mainPy    = Join-Path $installDir "intellieye.py"
# 가상환경의 python 을 직접 사용하여 실행 (PATH 의존 없음)
Set-Content -Path $runScript -Value "& `"$venvPython`" `"$mainPy`""
Write-Host "[OK] 런처 생성: $runScript" -ForegroundColor Green

# ── 6. PowerShell Profile에 intellieye 함수 등록 ──────────────────────────────
$profileContent = @"

# IntelliEye Agent
function intellieye {
    param([string]`$Command)
    `$venvPy = "$venvPython"
    if (-not (Test-Path `$venvPy)) { Write-Host "IntelliEye 가상환경을 찾을 수 없습니다. 재설치가 필요합니다." -ForegroundColor Red; return }
    if (`$Command -eq "update") {
        & `$venvPy "$mainPy" --update
    } else {
        & `$venvPy "$mainPy" `$Command
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
Write-Host "또는 직접 실행:" -ForegroundColor Cyan
Write-Host "  powershell `"$runScript`"" -ForegroundColor Yellow
Write-Host ""
Write-Host "※ 새 PowerShell 창을 열어야 'intellieye' 명령어가 활성화됩니다." -ForegroundColor Cyan
Write-Host ""
