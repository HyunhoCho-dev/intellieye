"""
intellieye.py — IntelliEye 메인 진입점
AI가 화면을 실시간으로 보면서 노트북을 제어하는 에이전트
Made by Hyunho Cho
"""

import sys

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


def main() -> None:
    print(BANNER)

    agent = select_model()
    print("\n  IntelliEye 준비 완료! 명령을 입력하세요.")
    print("  특수 명령: '종료' 또는 'exit' — 프로그램 종료")
    print("             '상태'            — 현재 화면 분석")
    print("             '모델변경'         — 모델 다시 선택\n")

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

        elif user_input == "상태":
            analyze_screen(agent)

        elif user_input == "모델변경":
            print()
            agent = select_model()
            print("  모델이 변경되었습니다.\n")

        else:
            # 자연어 목표 → 에이전트 루프 실행
            run_agent_loop(agent, user_input)


if __name__ == "__main__":
    main()
