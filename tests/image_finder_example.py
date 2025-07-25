# 图像查找工具示例

import os
import sys
import time

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.screenshot_tool import ScreenshotTool
from tools.image_finder_tool import ImageFinderTool


def main():
    # 创建临时目录
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 截取屏幕
    screenshot_path = os.path.join(temp_dir, "screenshot.png")
    ScreenshotTool.capture_screen(screenshot_path)
    print(f"截图已保存到: {screenshot_path}")
    
    # 创建图像查找工具
    finder = ImageFinderTool(ocr_backend="easyocr")
    
    # 示例1：通过文本查找
    text_to_find = input("请输入要查找的文本: ")
    print(f"\n正在查找文本: '{text_to_find}'...")
    text_results = finder.find_text(screenshot_path, text_to_find)
    
    if text_results:
        print(f"找到 {len(text_results)} 个匹配的文本:")
        for i, result in enumerate(text_results):
            print(f"结果 {i+1}:")
            print(f"  文本: {result['text']}")
            print(f"  位置: 左上角({result['left']}, {result['top']}), 宽x高: {result['width']}x{result['height']}")
            print(f"  中心点: ({result['center_x']}, {result['center_y']})")
            print(f"  置信度: {result['conf']:.2f}")
    else:
        print(f"未找到匹配的文本: '{text_to_find}'")
    
    # 示例2：通过图像查找（需要用户提供模板图像）
    template_path = input("\n请输入模板图像路径（留空跳过）: ")
    if template_path and os.path.exists(template_path):
        print(f"正在查找图像: '{template_path}'...")
        image_results = finder.find_image(screenshot_path, template_path)
        
        if image_results:
            print(f"找到 {len(image_results)} 个匹配的图像:")
            for i, result in enumerate(image_results):
                print(f"结果 {i+1}:")
                print(f"  位置: 左上角({result['left']}, {result['top']}), 宽x高: {result['width']}x{result['height']}")
                print(f"  中心点: ({result['center_x']}, {result['center_y']})")
                print(f"  置信度: {result['conf']:.2f}")
        else:
            print(f"未找到匹配的图像")
    
    print("\n示例完成")


if __name__ == "__main__":
    main()