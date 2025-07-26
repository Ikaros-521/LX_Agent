import os
import platform
from typing import Optional
import time
import ctypes

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

class ScreenshotTool:
    @staticmethod
    def capture_screen(output_path: str) -> str:
        """全屏截图"""
        if pyautogui:
            img = pyautogui.screenshot()
            img.save(output_path)
            return output_path
        elif ImageGrab:
            img = ImageGrab.grab()
            img.save(output_path)
            return output_path
        else:
            raise ImportError("请安装 pyautogui 或 pillow")

    @staticmethod
    def capture_region(x: int, y: int, width: int, height: int, output_path: str) -> str:
        """指定区域截图"""
        if pyautogui:
            img = pyautogui.screenshot(region=(x, y, width, height))
            img.save(output_path)
            return output_path
        elif ImageGrab:
            bbox = (x, y, x + width, y + height)
            img = ImageGrab.grab(bbox)
            img.save(output_path)
            return output_path
        else:
            raise ImportError("请安装 pyautogui 或 pillow")

    @staticmethod
    def capture_window(window_title: str, output_path: str) -> str:
        """指定窗口截图（仅支持Windows），请使用管理员权限运行"""
        if platform.system() != "Windows":
            raise NotImplementedError("窗口截图仅支持Windows平台")
        
        ctypes.windll.user32.SetProcessDPIAware()
        
        if gw is None or ImageGrab is None:
            raise ImportError("请安装 pygetwindow 和 pillow")
        win = None
        for w in gw.getWindowsWithTitle(window_title):
            win = w
            break
        if not win:
            raise ValueError(f"未找到窗口: {window_title}")
        if win.isMinimized:
            win.restore()
        win.activate()
        time.sleep(0.5)  # 等待窗口前置
        bbox = (win.left, win.top, win.right, win.bottom)
        img = ImageGrab.grab(bbox)
        img.save(output_path)
        return output_path 

def get_capabilities():
    return ["screenshot_tool"]

def get_tools():
    return [
        {
            "name": "screenshot",
            "description": "截图工具，支持全屏、区域、窗口截图",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "description": "保存图片的路径"},
                    "mode": {"type": "string", "enum": ["screen", "region", "window"], "description": "截图模式"},
                    "x": {"type": "integer", "description": "区域截图起点X坐标，可选"},
                    "y": {"type": "integer", "description": "区域截图起点Y坐标，可选"},
                    "width": {"type": "integer", "description": "区域截图宽度，可选"},
                    "height": {"type": "integer", "description": "区域截图高度，可选"},
                    "window_title": {"type": "string", "description": "窗口标题，仅窗口截图时需要"}
                },
                "required": ["output_path", "mode"]
            }
        }
    ]

def call_tool(name, arguments):
    if name == "screenshot":
        mode = arguments.get("mode")
        output_path = arguments.get("output_path")
        try:
            if mode == "screen":
                path = ScreenshotTool.capture_screen(output_path)
            elif mode == "region":
                x = arguments.get("x")
                y = arguments.get("y")
                width = arguments.get("width")
                height = arguments.get("height")
                if None in (x, y, width, height):
                    return {"status": "error", "error": "区域截图需提供x, y, width, height"}
                path = ScreenshotTool.capture_region(x, y, width, height, output_path)
            elif mode == "window":
                window_title = arguments.get("window_title")
                if not window_title:
                    return {"status": "error", "error": "窗口截图需提供window_title"}
                path = ScreenshotTool.capture_window(window_title, output_path)
            else:
                return {"status": "error", "error": f"未知截图模式: {mode}"}
            return {"status": "success", "image_path": path}
        except BaseException as e:
            return {"status": "error", "error": str(e)}
    else:
        return {"status": "error", "error": f"Unknown tool: {name}"} 