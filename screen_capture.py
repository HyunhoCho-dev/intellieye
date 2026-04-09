"""
screen_capture.py — IntelliEye
화면 캡처 및 base64 인코딩 유틸리티
Made by Hyunho Cho
"""

import base64
import io

try:
    import mss
    import mss.tools
    _USE_MSS = True
except ImportError:
    _USE_MSS = False

from PIL import Image, ImageGrab


def capture_screen() -> Image.Image:
    """현재 전체 화면을 캡처하여 PIL Image로 반환합니다."""
    if _USE_MSS:
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # 전체 가상 화면
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img
    else:
        return ImageGrab.grab()


def image_to_base64(img: Image.Image) -> str:
    """PIL Image를 PNG base64 문자열로 변환하여 모델 입력에 사용합니다."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
