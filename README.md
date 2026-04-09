# 👁️ IntelliEye

> **AI가 화면을 보면서 노트북을 제어하는 에이전트**

**Made by Hyunho Cho**

[![Python 3.10~3.12](https://img.shields.io/badge/Python-3.10~3.12-blue?logo=python)](https://www.python.org/downloads/release/python-3121/)
[![Gemma 4](https://img.shields.io/badge/Model-Gemma%204-orange?logo=google)](https://deepmind.google/models/gemma/gemma-4/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

---

## ⚡ 1분 설치 (Windows PowerShell)

PowerShell 창을 열고 아래 명령어 **한 줄**만 실행하세요:

```powershell
iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content
```

설치가 완료되면 아래 명령으로 실행합니다:

```powershell
powershell "$HOME\intellieye\run.ps1"
```

---

## 🎯 사용 방법

IntelliEye를 실행하면 PowerShell 창에서 AI 에이전트와 대화할 수 있습니다.

```
========================================
  IntelliEye - AI Screen Control Agent
  Made by Hyunho Cho
========================================
모델을 선택하세요:
  [1] Gemma 4 E4B (4.5B) - 권장: 노트북/PC
  [2] Gemma 4 E2B (2.3B) - 경량: 저사양/빠른속도
선택 (1 또는 2):
```

모델을 선택한 후 자연어로 명령을 입력합니다:

```
사용자 > 크롬 열고 유튜브에서 AI 영상 검색해줘
  [IntelliEye] click: 바탕화면의 크롬 아이콘 클릭
  [IntelliEye] type: 유튜브 URL 입력
  [IntelliEye] click: 검색창 클릭
  [IntelliEye] type: AI 영상 검색어 입력
  [IntelliEye] hotkey: Enter 키 입력
  ✅ 목표 달성 완료!
```

### 특수 명령어

| 명령어 | 동작 |
|--------|------|
| `종료` / `exit` | 프로그램 종료 |
| `상태` | 현재 화면 분석 및 설명 |
| `모델변경` | 모델 재선택 |

---

## 🤖 모델 비교

| | **Gemma 4 E4B** | **Gemma 4 E2B** |
|---|---|---|
| **파라미터** | ~4.5B | ~2.3B |
| **권장 환경** | 노트북 / PC | 저사양 PC / 빠른 응답 |
| **VRAM (INT4)** | ~3.6 GB | ~2.0 GB |
| **추론 속도** | 중간 | 빠름 |
| **화면 분석 정확도** | 높음 | 보통 |
| **HuggingFace ID** | `google/gemma-4-E4B-it` | `google/gemma-4-E2B-it` |

> 💡 처음 실행 시 HuggingFace에서 모델을 자동으로 다운로드합니다 (수 GB).

---

## 🖥️ 시스템 요구 사항

| 항목 | 최소 사양 | 권장 사양 |
|------|---------|---------|
| **OS** | Windows 10 이상 | Windows 11 |
| **Python** | 3.10 이상 | **3.11 또는 3.12** (3.13 부분 지원, **3.14+ 미지원**) |
| **RAM** | 8 GB | 16 GB |
| **GPU VRAM** | 4 GB (E2B) | 6 GB (E4B) |
| **저장 공간** | 10 GB | 20 GB |
| **인터넷** | 최초 모델 다운로드 필요 | — |

> ⚠️ **Python 3.10~3.12 필수**: PyTorch(torch)는 Python 3.13에서 부분 지원, **Python 3.14 이상은 미지원**입니다.  
> Python 3.14에서 설치 스크립트 실행 시 torch 단계에서 멈추거나 실패합니다.  
> [Python 3.12 다운로드](https://www.python.org/downloads/release/python-3121/) 후 재시도하세요.

---

## ⚙️ 동작 원리

```
사용자 입력 (PowerShell)
        │
        ▼
  화면 캡처 (mss / PIL)
        │
        ▼
  Gemma 4 E4B/E2B 추론
  (화면 이미지 + 목표 → JSON 액션)
        │
        ▼
  액션 실행 (PyAutoGUI)
  ┌──────────────────────┐
  │ click  / type        │
  │ hotkey / scroll      │
  │ screenshot / done    │
  └──────────────────────┘
        │
        ▼
  화면 변화 감지 → 반복
  (done 액션 시 완료)
```

---

## 🛡️ 안전 기능 (FAILSAFE)

IntelliEye는 `pyautogui.FAILSAFE = True`로 설정되어 있습니다.

> **마우스를 화면 모서리(왼쪽 위)로 빠르게 이동하면 에이전트가 즉시 중단됩니다.**

예기치 않은 동작이 발생할 경우 이 기능을 활용하세요. 또한 `Ctrl+C`로도 언제든지 중단할 수 있습니다.

---

## 📁 파일 구조

```
intellieye/
├── install.ps1        # 원클릭 설치 스크립트
├── intellieye.py      # 메인 진입점 (PowerShell 대화 UI)
├── screen_capture.py  # 화면 캡처 & base64 변환
├── model.py           # Gemma 4 에이전트 래퍼
├── controller.py      # 마우스/키보드 제어
├── requirements.txt   # Python 패키지 목록
└── README.md
```

---

## 🩺 문제 해결 (Troubleshooting)

### ⏳ `torch 설치 중...` 단계에서 멈춤 (Python 3.14 사용 시)

**증상**: `install.ps1` 실행 시 `torch / torchvision / torchaudio 설치 중...` 에서 수분 이상 아무 진행이 없음.

**원인**: PyTorch는 **Python 3.14 이상에 대한 사전 빌드(wheel) 패키지를 제공하지 않습니다**.  
wheel이 없으면 pip가 소스에서 빌드를 시도하거나 오랜 시간 검색하다 실패합니다.

**해결 방법**:

1. **Python 3.12 설치 (권장)**
   ```
   https://www.python.org/downloads/release/python-3121/
   ```
   - 설치 시 "Add Python to PATH" 체크
   - PowerShell 재시작 후 `install.ps1` 다시 실행

2. **이미 Python 3.12가 있는 경우 (`py` 런처 사용)**
   ```powershell
   py -3.12 --version        # 3.12 확인
   py -3.12 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

3. **현재 Python 버전 확인**
   ```powershell
   python --version
   py --list
   ```

---

### ❌ `RuntimeError: Tensor.item() cannot be called on meta tensors`

이 오류는 CPU 전용 환경(GPU 없음)에서 `device_map="auto"` 사용 시 모델 가중치가 meta 디바이스에 남아있을 때 발생합니다.

**해결 방법 1 — 안전 로드 모드 활성화 (권장)**

```powershell
# Windows PowerShell
$env:INTELLIEYE_SAFE_LOAD='1'
python intellieye.py
```

**해결 방법 2 — CPU 전용 모드 강제**

```powershell
$env:INTELLIEYE_DEVICE='cpu'
$env:INTELLIEYE_SAFE_LOAD='1'
python intellieye.py
```

**해결 방법 3 — 패키지 최신 버전 업데이트**

```powershell
pip install -U torch transformers accelerate
```

**해결 방법 4 — Python 버전 확인**

Python 3.14+는 현재 지원되지 않습니다. Python 3.13에서는 torch 설치가 실패하거나 오래 걸릴 수 있습니다.  
**Python 3.10~3.12 사용을 권장합니다.** [Python 3.12 다운로드](https://www.python.org/downloads/release/python-3121/)

```powershell
python --version
```

---

### 🩺 환경 진단 (doctor 명령)

`doctor` 명령으로 환경 정보를 확인할 수 있습니다.

```powershell
# CLI 인수로 실행
python intellieye.py doctor

# 또는 실행 중 입력
사용자 > doctor
```

출력 예시:

```
[IntelliEye] doctor — 환경 정보
  Python         : 3.11.9 (main, ...)
  torch          : 2.5.1
  transformers   : 4.48.0
  accelerate     : 1.2.0
  CUDA 사용 가능 : False
  INTELLIEYE_DEVICE    : (미설정)
  INTELLIEYE_SAFE_LOAD : (미설정)
```

---

## 🔧 수동 설치

> **주의**: Python 3.10~3.12 를 사용하세요. Python 3.14+는 torch wheel이 없어 설치가 실패합니다.

```powershell
# 1. 저장소 클론
git clone https://github.com/HyunhoCho-dev/intellieye.git
cd intellieye

# 2. pip 업그레이드
pip install --upgrade pip

# 3. torch 먼저 설치 (CPU 전용)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

# 4. 나머지 패키지 설치
pip install -r requirements.txt --no-cache-dir --timeout 120

# 5. 실행
python intellieye.py
```

---

<div align="center">
Made with ❤️ by <b>Hyunho Cho</b>
</div>