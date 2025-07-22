import ctypes
import time
from loguru import logger
from typing import Dict, Any, Optional



class MouseKeyboardTool:
    """
    键鼠模拟工具，支持基础的键盘和鼠标操作（Windows，ctypes实现）
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

    # 鼠标操作
    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        try:
            self.user32.SetCursorPos(x, y)
            return {"status": "success", "x": x, "y": y}
        except BaseException as e:
            logger.error(f"Failed to move mouse: {e}")
            return {"status": "error", "error": str(e)}

    def mouse_click(self, button: str = "left") -> Dict[str, Any]:
        try:
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            if button == "left":
                self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif button == "right":
                self.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                self.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            else:
                return {"status": "error", "error": "Unsupported button"}
            return {"status": "success", "button": button}
        except BaseException as e:
            logger.error(f"Failed to click mouse: {e}")
            return {"status": "error", "error": str(e)}

    def mouse_scroll(self, delta: int) -> Dict[str, Any]:
        try:
            MOUSEEVENTF_WHEEL = 0x0800
            self.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
            return {"status": "success", "delta": delta}
        except BaseException as e:
            logger.error(f"Failed to scroll mouse: {e}")
            return {"status": "error", "error": str(e)}

    # 键盘操作
    def key_press(self, key_code: int, duration: float = 0.05) -> Dict[str, Any]:
        try:
            KEYEVENTF_KEYDOWN = 0
            KEYEVENTF_KEYUP = 2
            self.user32.keybd_event(key_code, 0, KEYEVENTF_KEYDOWN, 0)
            time.sleep(duration)
            self.user32.keybd_event(key_code, 0, KEYEVENTF_KEYUP, 0)
            return {"status": "success", "key_code": key_code}
        except BaseException as e:
            logger.error(f"Failed to press key: {e}")
            return {"status": "error", "error": str(e)}

    def type_text(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        try:
            for char in text:
                vk = self.user32.VkKeyScanW(ord(char)) & 0xff
                self.key_press(vk)
                time.sleep(interval)
            return {"status": "success", "text": text}
        except BaseException as e:
            logger.error(f"Failed to type text: {e}")
            return {"status": "error", "error": str(e)} 