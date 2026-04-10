"""
intellieye.py — IntelliEye main entry point
AI agent that watches the screen in real time and controls the PC
Made by Hyunho Cho
"""

import os
import subprocess
import sys
import urllib.request

# Python version compatibility notice (3.13+ is experimental)
if sys.version_info >= (3, 13):
    print(
        f"ℹ️  Python {sys.version_info.major}.{sys.version_info.minor} detected.\n"
        "   IntelliEye supports Python 3.10+ (3.13+ is experimental).\n"
        "   Some torch/transformers builds may not yet support this version.\n"
        "   If you encounter issues, try: pip install -U torch transformers accelerate\n"
        "   For best results, use Python 3.12.\n"
    )

print("Loading IntelliEye modules...", flush=True)
from controller import execute_action
from model import GemmaAgent
from screen_capture import capture_screen, image_to_base64

BANNER = """
========================================
  IntelliEye - AI Screen Control Agent
  Made by Hyunho Cho
========================================
"""

MODEL_MENU = """Select a model:
  [1] Gemma 4 E4B (4.5B) - Recommended: laptop/PC
  [2] Gemma 4 E2B (2.3B) - Lightweight: low-spec / faster
Choice (1 or 2): """

UPDATE_FILES = [
    "intellieye.py",
    "screen_capture.py",
    "model.py",
    "controller.py",
    "requirements.txt",
]

BASE_URL = "https://raw.githubusercontent.com/HyunhoCho-dev/intellieye/main/"
INSTALL_DIR = os.path.join(os.path.expanduser("~"), "intellieye")


def update() -> None:
    """Download the latest files from GitHub and update IntelliEye."""
    print("\n[IntelliEye] Checking for updates...")
    updated = []
    failed = []
    for filename in UPDATE_FILES:
        url = BASE_URL + filename
        dest = os.path.join(INSTALL_DIR, filename)
        try:
            urllib.request.urlretrieve(url, dest)
            updated.append(filename)
            print(f"  ✅ {filename} updated")
        except Exception as e:
            failed.append(filename)
            print(f"  ❌ {filename} update failed: {e}")

    # Re-install requirements
    req_path = os.path.join(INSTALL_DIR, "requirements.txt")
    if os.path.exists(req_path):
        print("\n[IntelliEye] Updating packages...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path, "-q"],
            check=False,
        )
        if result.returncode != 0:
            print("  ⚠️  Some packages failed to update. Please check manually.")

    print(f"\n[IntelliEye] Update complete! ({len(updated)} file(s) updated)")
    if failed:
        print(f"  Failed: {', '.join(failed)}")
    print("[IntelliEye] Please restart IntelliEye to apply changes.\n")
    sys.exit(0)


def select_model() -> GemmaAgent:
    """Prompt the user to select a model and return a GemmaAgent."""
    while True:
        choice = input(MODEL_MENU).strip()
        if choice == "1":
            model_name = "E4B"
            break
        elif choice == "2":
            model_name = "E2B"
            break
        else:
            print("  Invalid choice. Please enter 1 or 2.")

    print(f"\n  Loading [{model_name}] model...")
    print("  This may take a while on first run (model download + load).")
    agent = GemmaAgent(model_name)
    return agent


def run_agent_loop(agent: GemmaAgent, goal: str) -> None:
    """
    Run the agent loop until the goal is achieved or the user interrupts.

    1. Capture screen
    2. Pass screen + goal to the model → get JSON action
    3. Execute action
    4. Print result
    5. Repeat until 'done' action
    """
    history = []
    print(f"\n  Goal: {goal}")
    print("  Agent is watching the screen and starting work... (stop: Ctrl+C)\n")

    try:
        while True:
            # 1. Capture screen
            print("  [IntelliEye] Capturing screen...", end="\r", flush=True)
            screen = capture_screen()

            # 2. Model inference
            print("  [IntelliEye] Analyzing screen...  ", end="\r", flush=True)
            action = agent.decide_action(screen, goal, history)

            # 3. Print action info
            desc = action.get("description", "")
            action_type = action.get("action", "")
            print(f"  [IntelliEye] {action_type}: {desc}          ")

            # 4. Execute action
            execute_action(action)
            history.append(f"{action_type}: {desc}")

            # 5. Exit on done
            if action_type == "done":
                print("\n  ✅ Goal achieved!")
                break

    except KeyboardInterrupt:
        print("\n  Agent loop stopped.")


def analyze_screen(agent: GemmaAgent) -> None:
    """Capture and analyze the current screen, printing the result."""
    print("\n  Analyzing current screen...", flush=True)
    screen = capture_screen()
    action = agent.decide_action(screen, "Describe the current screen state.", [])
    print(f"  [IntelliEye] Screen analysis: {action.get('description', '')}\n")


def doctor() -> None:
    """Print Python, torch, transformers versions, CUDA availability, and device info."""
    import importlib

    print("\n[IntelliEye] doctor — environment info")
    print(f"  Python    : {sys.version}")
    for pkg in ("torch", "transformers", "accelerate"):
        try:
            mod = importlib.import_module(pkg)
            print(f"  {pkg:<15}: {mod.__version__}")
        except ImportError:
            print(f"  {pkg:<15}: not installed")

    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        print(f"  CUDA available : {cuda_ok}")
        if cuda_ok:
            print(f"  CUDA device    : {torch.cuda.get_device_name(0)}")
        if hasattr(torch.backends, "mps"):
            print(f"  MPS available  : {torch.backends.mps.is_available()}")
    except ImportError:
        print("  torch is not installed — cannot check CUDA info.")

    env_device = os.environ.get("INTELLIEYE_DEVICE", "(not set)")
    env_safe = os.environ.get("INTELLIEYE_SAFE_LOAD", "(not set)")
    print(f"  INTELLIEYE_DEVICE    : {env_device}")
    print(f"  INTELLIEYE_SAFE_LOAD : {env_safe}")
    print()


def main() -> None:
    # Handle --update / --doctor arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--update":
            update()
        elif sys.argv[1] in ("doctor", "--doctor"):
            doctor()
            sys.exit(0)

    print(BANNER)

    try:
        agent = select_model()
    except RuntimeError as exc:
        if "meta" in str(exc).lower():
            print(
                "\n❌ Error: RuntimeError related to meta tensors.\n"
                f"   Cause: {exc}\n\n"
                "   Solutions:\n"
                "   1) Use safe-load mode (prevents meta tensors):\n"
                "        Windows PowerShell:\n"
                "          $env:INTELLIEYE_SAFE_LOAD='1'; python intellieye.py\n"
                "        CMD:\n"
                "          set INTELLIEYE_SAFE_LOAD=1 && python intellieye.py\n\n"
                "   2) Force CPU-only mode:\n"
                "        $env:INTELLIEYE_DEVICE='cpu'; $env:INTELLIEYE_SAFE_LOAD='1'; python intellieye.py\n\n"
                "   3) Update torch/transformers to the latest version:\n"
                "        pip install -U torch transformers\n\n"
                f"   4) Check Python version (currently: Python {sys.version_info.major}.{sys.version_info.minor})\n"
                "        pip install -U torch transformers accelerate\n"
            )
            sys.exit(1)
        raise

    print("\n  IntelliEye is ready! Enter a command below.")
    print("  Special commands:")
    print("    exit / quit   — quit the program")
    print("    status        — analyze the current screen")
    print("    change-model  — switch to a different model")
    print("    update        — update to the latest version")
    print("    doctor        — show environment info\n")

    while True:
        try:
            user_input = input("User > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting.")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "종료"):
            print("  Goodbye!")
            sys.exit(0)

        elif user_input.strip().lower() == "update":
            update()

        elif user_input.strip().lower() == "doctor":
            doctor()

        elif user_input.lower() in ("status", "상태"):
            analyze_screen(agent)

        elif user_input.lower() in ("change-model", "모델변경"):
            print()
            try:
                agent = select_model()
            except RuntimeError as exc:
                if "meta" in str(exc).lower():
                    print(
                        f"\n❌ Model load error (meta tensor): {exc}\n"
                        "   Set INTELLIEYE_SAFE_LOAD=1 and try again.\n"
                    )
                    continue
                raise
            print("  Model changed.\n")

        else:
            # Natural-language goal → run agent loop
            try:
                run_agent_loop(agent, user_input)
            except RuntimeError as exc:
                if "meta" in str(exc).lower():
                    print(
                        f"\n❌ Meta tensor error during inference: {exc}\n"
                        "   Set INTELLIEYE_SAFE_LOAD=1 and restart IntelliEye.\n"
                    )
                else:
                    raise


if __name__ == "__main__":
    main()
