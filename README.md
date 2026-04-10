# 👁️ IntelliEye

> **AI agent that watches the screen in real time and controls your PC**

**Made by Hyunho Cho**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/downloads/release/python-3121/)
[![Gemma 3n](https://img.shields.io/badge/Model-Gemma%203n-orange?logo=google)](https://deepmind.google/models/gemma/gemma-3n/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

---

## ⚡ One-line install (Windows PowerShell)

Open a PowerShell window and run **just this one command**:

```powershell
iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content
```

### 🔄 Automatic Python 3.12 setup

The installer automatically locates Python 3.12 for you.

| Situation | Behavior |
|-----------|----------|
| Python 3.12 already installed | Used immediately (`py -3.12` or PATH) |
| Python 3.12 missing + winget available | Python 3.12 installed automatically via winget |
| Only Python 3.14 + no winget | Clear error message with manual install steps |

> ⚠️ **Python 3.14+ is not supported.** PyTorch pre-built wheels are not available for it — installation will fail.
> The installer handles this automatically by targeting Python 3.12, so you can run the one-liner as-is even if only Python 3.14 is installed.

When installation completes, start IntelliEye by opening a **new** PowerShell window and typing:

```powershell
intellieye
```

> 💡 The installer registers `intellieye` as a command automatically (via `.cmd` launcher + PowerShell profile). No PATH editing required — just open a new window.

Or run it directly:

```powershell
powershell "$HOME\intellieye\run.ps1"
```

---

## 🎯 Usage

### Launching IntelliEye

After installation, open a **new** PowerShell window and type:

```powershell
intellieye
```

The `intellieye` command is registered automatically by the installer. No additional setup is needed — just close the installer window and open a fresh one.

After launching IntelliEye you interact with the AI agent in the PowerShell window.

```
========================================
  IntelliEye - AI Screen Control Agent
  Made by Hyunho Cho
========================================
Select a model:
  [1] Gemma 3n E4B (4.5B) - Recommended: laptop/PC
  [2] Gemma 3n E2B (2.3B) - Lightweight: low-spec / faster
Choice (1 or 2):
```

After selecting a model, type natural-language commands:

```
User > Open Chrome and search YouTube for AI videos
  [IntelliEye] click: Click the Chrome icon on the desktop
  [IntelliEye] type: Type YouTube URL
  [IntelliEye] click: Click the search bar
  [IntelliEye] type: Type AI video search term
  [IntelliEye] hotkey: Press Enter
  ✅ Goal achieved!
```

### Special commands

| Command | Action |
|---------|--------|
| `exit` / `quit` | Quit the program |
| `status` | Analyze and describe the current screen |
| `change-model` | Switch to a different model |
| `update` | Update to the latest version |
| `doctor` | Show environment diagnostics |

### Progress indicators

IntelliEye reports what it is doing at every step so you always know it is working:

- **Startup** — "Loading IntelliEye modules..."
- **Model load** — "Loading processor...", "Loading model weights (this may take a while)..."
- **First run** — "(First run: downloading model weights — this may take several minutes...)"
- **Agent loop** — "Capturing screen...", "Analyzing screen..." (updated in real time)
- **Result** — action type and description printed for every step

---

## 🤖 Model comparison

| | **Gemma 3n E4B** | **Gemma 3n E2B** |
|---|---|---|
| **Parameters** | ~4.5 B (effective) | ~2.3 B (effective) |
| **Recommended for** | Laptop / PC | Low-spec PC / faster responses |
| **VRAM (INT4)** | ~3.6 GB | ~2.0 GB |
| **Inference speed** | Medium | Fast |
| **Screen analysis accuracy** | High | Moderate |
| **Multimodal** | ✅ Image + text | ✅ Image + text |
| **HuggingFace ID** | `google/gemma-3n-E4B-it` | `google/gemma-3n-E2B-it` |

> 💡 Gemma 3n is Google's on-device multimodal model with native image understanding support — ideal for real-time screen analysis.

> On first run, model weights are downloaded automatically from HuggingFace (several GB).

---

## 🖥️ System requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| **OS** | Windows 10 or later | Windows 11 |
| **Python** | **3.12** (auto-installed by installer) | **3.12** (3.13 partial support; **3.14+ not supported**) |
| **RAM** | 8 GB | 16 GB |
| **GPU VRAM** | 4 GB (E2B) | 6 GB (E4B) |
| **Storage** | 10 GB | 20 GB |
| **Internet** | Required for initial model download | — |

> ⚠️ **Python 3.12 required**: PyTorch partially supports Python 3.13 and **does not support Python 3.14+**.
> The installer automatically finds Python 3.12 and installs it via `winget` if needed.
> You can safely run the one-liner even if only Python 3.14 is installed.

---

## ⚙️ How it works

```
User input (PowerShell)
        │
        ▼
  Screen capture (mss / PIL)
        │
        ▼
  Gemma 3n E4B/E2B inference
  (screen image + goal → JSON action)
  [multimodal: image + text → text]
        │
        ▼
  Action execution (PyAutoGUI)
  ┌──────────────────────┐
  │ click  / type        │
  │ hotkey / scroll      │
  │ screenshot / done    │
  └──────────────────────┘
        │
        ▼
  Detect screen change → repeat
  (stops on 'done' action)
```

---

## 🛡️ Safety (FAILSAFE)

IntelliEye runs with `pyautogui.FAILSAFE = True`.

> **Move the mouse to the top-left corner of the screen to immediately stop the agent.**

Use this if the agent behaves unexpectedly. You can also press `Ctrl+C` at any time.

---

## 📁 File structure

```
intellieye/
├── install.ps1        # One-click installer script
├── intellieye.py      # Main entry point (PowerShell dialog UI)
├── screen_capture.py  # Screen capture & base64 conversion
├── model.py           # Gemma 3n agent wrapper
├── controller.py      # Mouse/keyboard control
├── requirements.txt   # Python package list
└── README.md
```

---

## 🩺 Troubleshooting

### ⏳ Stuck at "Upgrading pip / setuptools / wheel..."

**Symptom**: `install.ps1` appears frozen at the pip upgrade step (especially when reusing an existing virtual environment).

**Root causes (any of these can cause silent waiting):**
1. pip is connecting to PyPI to check for newer versions — network latency causes a pause with no output.
2. The existing `.venv` was created by a different Python version (e.g. Python 3.14) and is incompatible with Python 3.12.
3. Output buffering prevents pip progress from appearing in the terminal.

**Updated installer behavior** (current version):

- Sets `PYTHONUNBUFFERED=1` so Python output appears immediately.
- Uses `pip install -v` so every step ("Collecting pip", "Downloading …", "Installing …") is printed.
- Validates the existing `.venv` Python version **before** starting pip operations; if wrong, recreates the venv automatically.
- Adds `--timeout 60 --no-cache-dir` to avoid silent hangs from stale cache reads or slow server responses.

If the step still takes over 2 minutes with no output:

```powershell
# Remove the old venv and start fresh
Remove-Item -Recurse -Force "$HOME\intellieye\.venv" -ErrorAction SilentlyContinue
iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content
```

### ⏳ Stuck at "Installing torch..." (Python 3.14)

**Symptom**: `install.ps1` appears frozen at the `torch / torchvision / torchaudio` step for several minutes.

**Cause**: PyTorch provides no pre-built wheel for Python 3.14+. pip either attempts a source build (which can take a very long time) or silently searches without result.

**Updated installer behavior** (current version):

The installer detects Python 3.14 and **automatically locates or installs Python 3.12** before proceeding.

1. Checks for `py -3.12`
2. If missing, installs via `winget install Python.Python.3.12`
3. Creates a `.venv` with Python 3.12
4. Installs torch inside that virtual environment

**Just run the one-liner and let the installer handle it:**

```powershell
iex (iwr -useb https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/install.ps1).Content
```

**If automatic installation fails, fix it manually:**

1. **Install Python 3.12 (recommended)**
   ```
   https://www.python.org/downloads/release/python-3121/
   ```
   - Check "Add Python to PATH" or "py launcher" during install.
   - Restart PowerShell and re-run `install.ps1`.

2. **Verify Python 3.12 is available**
   ```powershell
   py -3.12 --version   # should show 3.12.x
   py --list            # list all installed versions
   ```

---

### ⏳ Startup looks frozen (model loading)

**Symptom**: Running `run.ps1` prints the version notice then appears to hang.

**Cause**: The first time you run IntelliEye it must download several GB of model weights from HuggingFace. This is normal and can take 5–30 minutes depending on your connection.

**What you will see during normal operation:**

```
Loading IntelliEye modules...
  Loading model: google/gemma-3n-E4B-it
  (First run: downloading model weights — this may take several minutes...)
  Device: cpu
  Loading processor...
  Loading model weights (this may take a while)...
  ✅ Model loaded successfully!
```

If the terminal shows these messages and is progressing (disk/network activity visible), the app is **not hung** — it is downloading or loading weights. Please wait.

---

### ❌ `RuntimeError: Tensor.item() cannot be called on meta tensors`

This occurs in CPU-only environments (no GPU) when `device_map="auto"` leaves weights on the meta device.

**Solution 1 — Enable safe-load mode (recommended)**

```powershell
# Windows PowerShell
$env:INTELLIEYE_SAFE_LOAD='1'
python intellieye.py
```

**Solution 2 — Force CPU-only mode**

```powershell
$env:INTELLIEYE_DEVICE='cpu'
$env:INTELLIEYE_SAFE_LOAD='1'
python intellieye.py
```

**Solution 3 — Update packages**

```powershell
pip install -U torch transformers accelerate
```

**Solution 4 — Check Python version**

Python 3.14+ is not supported. Use Python 3.12.
Run the installer again to set up Python 3.12 automatically.

```powershell
python --version
```

---

### 🩺 Environment diagnostics (`doctor` command)

```powershell
# As a CLI argument
python intellieye.py doctor

# Or while running
User > doctor
```

Example output:

```
[IntelliEye] doctor — environment info
  Python         : 3.12.4 (main, ...)
  torch          : 2.5.1
  transformers   : 4.48.0
  accelerate     : 1.2.0
  CUDA available : False
  INTELLIEYE_DEVICE    : (not set)
  INTELLIEYE_SAFE_LOAD : (not set)
```

---

## 🔧 Manual installation

> **Important**: Use **Python 3.12**. Python 3.14+ lacks torch wheels and will fail.
> Use `install.ps1` for automatic setup.

```powershell
# 1. Clone the repo
git clone https://github.com/HyunhoCho-dev/intellieye.git
cd intellieye

# 2. Create a Python 3.12 virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\activate

# 3. Upgrade pip / setuptools / wheel
pip install --upgrade pip setuptools wheel

# 4. Install torch first (CPU build)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

# 5. Install remaining packages
pip install -r requirements.txt --no-cache-dir --timeout 120

# 6. Run
python intellieye.py
```

---

<div align="center">
Made with ❤️ by <b>Hyunho Cho</b>
</div>