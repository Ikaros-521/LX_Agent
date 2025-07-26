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

def get_capabilities():
    return ["mouse_keyboard_tool"]

def get_tools():
    return [
        {
            "name": "move_mouse",
            "description": "移动鼠标到指定坐标",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X坐标"},
                    "y": {"type": "integer", "description": "Y坐标"}
                },
                "required": ["x", "y"]
            }
        },
        {
            "name": "mouse_click",
            "description": "点击鼠标（支持left/right）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "button": {"type": "string", "enum": ["left", "right"], "description": "鼠标按键"}
                },
                "required": ["button"]
            }
        },
        {
            "name": "mouse_scroll",
            "description": "鼠标滚轮滚动",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "delta": {"type": "integer", "description": "滚动的距离（正负表示方向）"}
                },
                "required": ["delta"]
            }
        },
        {
            "name": "key_press",
            "description": "按下键盘按键（通过key_code）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "key_code": {"type": "integer", "description": "虚拟键码（VK）"},
                    "duration": {"type": "number", "description": "按下持续时间（秒）", "default": 0.05}
                },
                "required": ["key_code"]
            }
        },
        {
            "name": "type_text",
            "description": "输入一串文本（逐字模拟键盘）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要输入的文本"},
                    "interval": {"type": "number", "description": "每个字符间隔（秒）", "default": 0.05}
                },
                "required": ["text"]
            }
        }
    ]

def call_tool(name, arguments):
    tool = MouseKeyboardTool()
    if name == "move_mouse":
        return tool.move_mouse(arguments.get("x"), arguments.get("y"))
    elif name == "mouse_click":
        return tool.mouse_click(arguments.get("button", "left"))
    elif name == "mouse_scroll":
        return tool.mouse_scroll(arguments.get("delta", 0))
    elif name == "key_press":
        return tool.key_press(arguments.get("key_code"), arguments.get("duration", 0.05))
    elif name == "type_text":
        return tool.type_text(arguments.get("text"), arguments.get("interval", 0.05))
    else:
        return {"status": "error", "error": f"Unknown tool: {name}"} 