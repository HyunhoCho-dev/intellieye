"""
intellieye.py — IntelliEye 메인 진입점
AI가 화면을 실시간으로 보면서 노트북을 제어하는 에이전트
Made by Hyunho Cho
"""

import os
import subprocess
import sys
import urllib.request

# Python 버전 경고 (3.13+ 는 일부 torch/transformers 빌드와 호환되지 않을 수 있음)
if sys.version_info >= (3, 13):
    print(
        f"⚠️  경고: Python {sys.version_info.major}.{sys.version_info.minor}이(가) 감지되었습니다.\n"
        "   IntelliEye는 Python 3.10~3.12에서 가장 안정적으로 동작합니다.\n"
        "   현재 버전에서 오류가 발생하면 Python 3.11 또는 3.12로 재설치하세요.\n"
        "   참고: https://www.python.org/downloads/\n"
    )

from controller import execute_action
from model import GemmaAgent
from screen_capture import capture_screen, image_to_base64

BANNER = """
========================================
  IntelliEye - AI Screen Control Agent
  Made by Hyunho Cho
========================================
"""

MODEL_MENU = """모델을 선택하세요:
  [1] Gemma 4 E4B (4.5B) - 권장: 노트북/PC
  [2] Gemma 4 E2B (2.3B) - 경량: 저사양/빠른속도
선택 (1 또는 2): """

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
    """GitHub에서 최신 파일을 내려받아 IntelliEye를 업데이트합니다."""
    print("\n[IntelliEye] 업데이트 확인 중...")
    updated = []
    failed = []
    for filename in UPDATE_FILES:
        url = BASE_URL + filename
        dest = os.path.join(INSTALL_DIR, filename)
        try:
            urllib.request.urlretrieve(url, dest)
            updated.append(filename)
            print(f"  ✅ {filename} 업데이트 완료")
        except Exception as e:
            failed.append(filename)
            print(f"  ❌ {filename} 업데이트 실패: {e}")

    # requirements 재설치
    req_path = os.path.join(INSTALL_DIR, "requirements.txt")
    if os.path.exists(req_path):
        print("\n[IntelliEye] 패키지 업데이트 중...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path, "-q"],
            check=False,
        )
        if result.returncode != 0:
            print("  ⚠️  일부 패키지 업데이트에 실패했습니다. 수동으로 확인해 주세요.")

    print(f"\n[IntelliEye] 업데이트 완료! ({len(updated)}개 파일 업데이트)")
    if failed:
        print(f"  실패: {', '.join(failed)}")
    print("[IntelliEye] 변경사항 적용을 위해 intellieye를 다시 실행하세요.\n")
    sys.exit(0)


def select_model() -> GemmaAgent:
    """사용자에게 모델을 선택하게 하고 GemmaAgent를 반환합니다."""
    while True:
        choice = input(MODEL_MENU).strip()
        if choice == "1":
            model_name = "E4B"
            break
        elif choice == "2":
            model_name = "E2B"
            break
        else:
            print("  잘못된 입력입니다. 1 또는 2를 입력하세요.")

    print(f"\n  [{model_name}] 모델을 로딩합니다...")
    agent = GemmaAgent(model_name)
    return agent


def run_agent_loop(agent: GemmaAgent, goal: str) -> None:
    """
    목표가 달성되거나 사용자가 중단할 때까지 에이전트 루프를 실행합니다.

    1. 화면 캡처
    2. 모델에 화면 + 목표 전달 → JSON 액션 획득
    3. 액션 실행
    4. 결과 출력
    5. done 액션이 될 때까지 반복
    """
    history = []
    print(f"\n  목표: {goal}")
    print("  에이전트가 화면을 보면서 작업을 시작합니다... (중단: Ctrl+C)\n")

    try:
        while True:
            # 1. 화면 캡처
            screen = capture_screen()

            # 2. 모델 추론
            action = agent.decide_action(screen, goal, history)

            # 3. 액션 정보 출력
            desc = action.get("description", "")
            action_type = action.get("action", "")
            print(f"  [IntelliEye] {action_type}: {desc}")

            # 4. 액션 실행
            execute_action(action)
            history.append(f"{action_type}: {desc}")

            # 5. done이면 종료
            if action_type == "done":
                print("\n  ✅ 목표 달성 완료!")
                break

    except KeyboardInterrupt:
        print("\n  에이전트 루프가 중단되었습니다.")


def analyze_screen(agent: GemmaAgent) -> None:
    """현재 화면을 캡처하여 분석 결과를 출력합니다."""
    print("\n  화면을 분석 중입니다...")
    screen = capture_screen()
    action = agent.decide_action(screen, "현재 화면 상태를 설명해주세요.", [])
    print(f"  [IntelliEye] 화면 분석: {action.get('description', '')}\n")


def doctor() -> None:
    """Python, torch, transformers 버전과 CUDA 가용성, 모델 파라미터 디바이스를 출력합니다."""
    import importlib

    print("\n[IntelliEye] doctor — 환경 정보")
    print(f"  Python    : {sys.version}")
    for pkg in ("torch", "transformers", "accelerate"):
        try:
            mod = importlib.import_module(pkg)
            print(f"  {pkg:<15}: {mod.__version__}")
        except ImportError:
            print(f"  {pkg:<15}: 설치되지 않음")

    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        print(f"  CUDA 사용 가능: {cuda_ok}")
        if cuda_ok:
            print(f"  CUDA 장치    : {torch.cuda.get_device_name(0)}")
        if hasattr(torch.backends, "mps"):
            print(f"  MPS 사용 가능 : {torch.backends.mps.is_available()}")
    except ImportError:
        print("  torch가 설치되어 있지 않아 CUDA 정보를 확인할 수 없습니다.")

    env_device = os.environ.get("INTELLIEYE_DEVICE", "(미설정)")
    env_safe = os.environ.get("INTELLIEYE_SAFE_LOAD", "(미설정)")
    print(f"  INTELLIEYE_DEVICE    : {env_device}")
    print(f"  INTELLIEYE_SAFE_LOAD : {env_safe}")
    print()


def main() -> None:
    # --update / --doctor 인수 처리
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
                "\n❌ 오류: meta 텐서 관련 RuntimeError가 발생했습니다.\n"
                f"   원인: {exc}\n\n"
                "   해결 방법:\n"
                "   1) 안전 로드 모드 사용 (meta 텐서 방지):\n"
                "        Windows PowerShell:\n"
                "          $env:INTELLIEYE_SAFE_LOAD='1'; python intellieye.py\n"
                "        CMD:\n"
                "          set INTELLIEYE_SAFE_LOAD=1 && python intellieye.py\n\n"
                "   2) CPU 전용 모드 강제:\n"
                "        $env:INTELLIEYE_DEVICE='cpu'; $env:INTELLIEYE_SAFE_LOAD='1'; python intellieye.py\n\n"
                "   3) torch/transformers 최신 버전으로 업데이트:\n"
                "        pip install -U torch transformers\n\n"
                "   4) Python 3.11 또는 3.12 사용 권장 (현재: "
                f"Python {sys.version_info.major}.{sys.version_info.minor})\n"
            )
            sys.exit(1)
        raise

    print("\n  IntelliEye 준비 완료! 명령을 입력하세요.")
    print("  특수 명령: '종료' 또는 'exit' — 프로그램 종료")
    print("             '상태'            — 현재 화면 분석")
    print("             '모델변경'         — 모델 다시 선택")
    print("             'update'          — 최신 버전으로 업데이트")
    print("             'doctor'          — 환경 정보 출력\n")

    while True:
        try:
            user_input = input("사용자 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  종료합니다.")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("종료", "exit"):
            print("  IntelliEye를 종료합니다. 안녕히 가세요!")
            sys.exit(0)

        elif user_input.strip().lower() == "update":
            update()

        elif user_input.strip().lower() == "doctor":
            doctor()

        elif user_input == "상태":
            analyze_screen(agent)

        elif user_input == "모델변경":
            print()
            try:
                agent = select_model()
            except RuntimeError as exc:
                if "meta" in str(exc).lower():
                    print(
                        f"\n❌ 모델 로딩 오류 (meta 텐서): {exc}\n"
                        "   INTELLIEYE_SAFE_LOAD=1 환경 변수를 설정하고 다시 시도하세요.\n"
                    )
                    continue
                raise
            print("  모델이 변경되었습니다.\n")

        else:
            # 자연어 목표 → 에이전트 루프 실행
            try:
                run_agent_loop(agent, user_input)
            except RuntimeError as exc:
                if "meta" in str(exc).lower():
                    print(
                        f"\n❌ 추론 중 meta 텐서 오류: {exc}\n"
                        "   INTELLIEYE_SAFE_LOAD=1 환경 변수를 설정하고 intellieye를 재시작하세요.\n"
                    )
                else:
                    raise


if __name__ == "__main__":
    main()
