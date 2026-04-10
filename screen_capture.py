"""
screen_capture.py — IntelliEye
Screen capture and base64 encoding utilities
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
    """Capture the full screen and return it as a PIL Image."""
    if _USE_MSS:
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # full virtual screen
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img
    else:
        return ImageGrab.grab()


def image_to_base64(img: Image.Image) -> str:
    """Convert a PIL Image to a PNG base64 string for use as model input."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
