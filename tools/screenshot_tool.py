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