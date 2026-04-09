"""
controller.py — IntelliEye
PyAutoGUI 기반 마우스/키보드 제어 모듈
Made by Hyunho Cho
"""

import time

import pyautogui
import pyperclip

pyautogui.FAILSAFE = True

# ASCII 범위 경계값 — 이 값을 초과하는 문자는 유니코드(한글 등)로 간주합니다.
ASCII_MAX = 127


def execute_action(action: dict) -> str:
    """
    모델이 결정한 액션 딕셔너리를 실행하고 설명 문자열을 반환합니다.

    지원 액션:
      {"action":"click",      "x":int, "y":int, "description":str}
      {"action":"type",       "text":str, "description":str}
      {"action":"hotkey",     "keys":[str], "description":str}
      {"action":"scroll",     "direction":str, "amount":int, "description":str}
      {"action":"screenshot", "description":str}
      {"action":"done",       "description":str}
    """
    action_type = action.get("action", "")
    description = action.get("description", "")

    if action_type == "click":
        x = int(action.get("x", 0))
        y = int(action.get("y", 0))
        pyautogui.click(x, y)
        time.sleep(0.5)

    elif action_type == "type":
        text = action.get("text", "")
        # 한글/유니코드 텍스트는 클립보드를 통해 붙여넣기
        if any(ord(c) > ASCII_MAX for c in text):
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.typewrite(text, interval=0.05)
        time.sleep(0.5)

    elif action_type == "hotkey":
        keys = action.get("keys", [])
        if keys:
            pyautogui.hotkey(*keys)
        time.sleep(0.5)

    elif action_type == "scroll":
        direction = action.get("direction", "down")
        amount = int(action.get("amount", 3))
        pyautogui.scroll(amount if direction == "up" else -amount)
        time.sleep(0.5)

    elif action_type == "screenshot":
        # 화면 분석만 요청하는 액션 (캡처는 메인 루프에서 처리)
        time.sleep(0.5)

    elif action_type == "done":
        return description

    return description
