import ctypes
ctypes.windll.user32.SetProcessDPIAware()
from tools.screenshot_tool import ScreenshotTool
import time

if __name__ == '__main__':
    window_title = input('请输入要截图的窗口标题: ')
    # time.sleep(3)
    output_path = 'test_window_screenshot.png'
    try:
        # 截图前后打印窗口坐标
        import pygetwindow as gw
        win = None
        for w in gw.getWindowsWithTitle(window_title):
            win = w
            break
        if not win:
            print(f'未找到窗口: {window_title}')
        else:
            win.activate()
            win.restore()
            time.sleep(0.5)  # 给窗口前置一点缓冲时间
            print(f'截图前窗口坐标: left={win.left}, top={win.top}, right={win.right}, bottom={win.bottom}')
            result = ScreenshotTool.capture_window(window_title, output_path)
            # 截图后再打印一次坐标
            for w in gw.getWindowsWithTitle(window_title):
                win = w
                break
            print(f'截图后窗口坐标: left={win.left}, top={win.top}, right={win.right}, bottom={win.bottom}')
            print(f'截图已保存到: {result}')
    except Exception as e:
        print(f'发生异常: {e}') 