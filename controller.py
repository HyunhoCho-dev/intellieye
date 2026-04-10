"""
controller.py — IntelliEye
PyAutoGUI-based mouse/keyboard control module
Made by Hyunho Cho
"""

import time

import pyautogui
import pyperclip

pyautogui.FAILSAFE = True

# Characters above this codepoint are treated as Unicode (e.g., non-ASCII scripts).
ASCII_MAX = 127


def execute_action(action: dict) -> str:
    """
    Execute the action dictionary decided by the model and return a description string.

    Supported actions:
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
        # Non-ASCII text is pasted via clipboard to handle Unicode correctly
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
        # Screen-analysis-only action (capture is handled in the main loop)
        time.sleep(0.5)

    elif action_type == "done":
        return description

    return description
