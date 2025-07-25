# 本地MCP适配器实现

import subprocess
import platform
import os
from typing import Dict, Any, List, Optional
import asyncio
from tools.sleep_tool import sleep_tool

from mcp_server.base import BaseMCP

class LocalMCPAdapter(BaseMCP):
    """
    本地MCP适配器，用于在本地执行命令
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化本地MCP适配器
        
        Args:
            config: MCP配置信息
        """
        self.config = config
        self.capabilities = config.get("capabilities", [])
        self.connected = False
        self.system = platform.system()
    
    async def connect(self) -> bool:
        """
        连接到本地MCP
        
        Returns:
            bool: 连接是否成功
        """
        # 本地MCP不需要实际连接，只需检查环境
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        """
        断开本地MCP连接
        """
        self.connected = False
    
    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        执行本地命令
        
        Args:
            command: 要执行的命令
            **kwargs: 命令参数
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        if not self.connected:
            raise ConnectionError("Not connected to local MCP")
        
        try:
            # 根据不同操作系统选择shell
            shell = True if self.system == "Windows" else False
            
            # 执行命令
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **kwargs
            )
            
            stdout, stderr = process.communicate()
            return {
                "status": "success" if process.returncode == 0 else "error",
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except BaseException as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        获取本地MCP状态
        
        Returns:
            Dict[str, Any]: MCP状态信息
        """
        return {
            "status": "connected" if self.connected else "disconnected",
            "system": self.system,
            "capabilities": self.capabilities
        }
    
    async def get_capabilities(self) -> List[str]:
        """
        返回本地MCP支持的能力列表
        
        Returns:
            List[str]: 能力列表
        """
        return self.capabilities
    
    async def is_available(self) -> bool:
        """
        检查本地MCP是否可用
        
        Returns:
            bool: MCP是否可用
        """
        return self.connected

    async def list_tools(self) -> Dict[str, Any]:
        """
        返回本地MCP支持的工具列表，符合MCP协议标准
        """
        tools = []
        if "file_tool" in self.capabilities:
            tools.append({
                "name": "list_directory",
                "description": "列出目录内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "目录路径"}
                    },
                    "required": ["path"]
                }
            })
            
            tools.append({
                "name": "read_file",
                "description": "读取文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"}
                    },
                    "required": ["path"]
                }
            })
        if "process_tool" in self.capabilities:
            tools.append({
                "name": "start_process",
                "description": "启动进程",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "要执行的命令"}
                    },
                    "required": ["command"]
                }
            })

            tools.append({
                "name": "execute_shell",
                "description": "执行Shell命令",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "要执行的命令"}
                    },
                    "required": ["command"]
                }
            })
        if "mouse_keyboard_tool" in self.capabilities:
            tools.append({
                "name": "mouse_click",
                "description": "点击鼠标",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X坐标"},
                        "y": {"type": "integer", "description": "Y坐标"},
                        "button": {"type": "string", "enum": ["left", "right"], "description": "鼠标按键"}
                    },
                    "required": ["x", "y"]
                }
            })
            
            tools.append({
                "name": "move_mouse",
                "description": "移动鼠标",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X坐标"},
                        "y": {"type": "integer", "description": "Y坐标"}
                    },
                    "required": ["x", "y"]
                }
            })
            
            tools.append({
                "name": "key_press",
                "description": "按下键盘按键",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "按键名称或字符"}
                    },
                    "required": ["key"]
                }
            })
        if "sleep_tool" in self.capabilities:
            tools.append({
                "name": "sleep",
                "description": "异步睡眠指定时间（ms或s）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ms": {"type": "integer", "description": "毫秒，可选"},
                        "s": {"type": "number", "description": "秒，可选"}
                    },
                    "anyOf": [
                        {"required": ["ms"]},
                        {"required": ["s"]}
                    ]
                }
            })
        if "ocr_tool" in self.capabilities:
            tools.append({
                "name": "ocr",
                "description": "OCR识别图片中的文字（支持多后端和多语言，lang如'ch_sim'、'en'、'ch_sim+en'）。detailed=True时返回每个文本的坐标、置信度等结构化信息，detailed=False时仅返回纯文本。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string", "description": "图片文件路径"},
                        "backend": {"type": "string", "description": "OCR后端，可选：tesseract、easyocr", "default": "easyocr"},
                        "lang": {"type": "string", "description": "OCR语言，如'ch_sim'、'en'、'ch_sim+en'，可选"},
                        "detailed": {"type": "boolean", "description": "是否返回详细结构化数据和坐标，True时返回每个文本的坐标、置信度等信息，False时仅返回纯文本", "default": False}
                    },
                    "required": ["image_path"]
                }
            })
        if "screenshot_tool" in self.capabilities:
            tools.append({
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
            })
        if "image_finder_tool" in self.capabilities:
            tools.append({
                "name": "find_text_pos",
                "description": "在图像中查找指定文本的位置",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string", "description": "图像路径"},
                        "text": {"type": "string", "description": "要查找的文本"},
                        "threshold": {"type": "number", "description": "匹配阈值，越高要求越精确", "default": 0.7},
                        "ocr_backend": {"type": "string", "description": "OCR后端，可选：tesseract、easyocr", "default": "easyocr"},
                        "lang": {"type": "string", "description": "OCR语言，如'ch_sim'、'en'、'ch_sim+en'，可选"}
                    },
                    "required": ["image_path", "text"]
                }
            })
            
            tools.append({
                "name": "find_image_pos",
                "description": "在图像中查找模板图像的位置（模板匹配）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string", "description": "要搜索的图像路径"},
                        "template_path": {"type": "string", "description": "模板图像路径"},
                        "threshold": {"type": "number", "description": "匹配阈值，越高要求越精确", "default": 0.8},
                        "ocr_backend": {"type": "string", "description": "OCR后端，可选：tesseract、easyocr", "default": "easyocr"},
                        "lang": {"type": "string", "description": "OCR语言，如'ch_sim'、'en'、'ch_sim+en'，可选"}
                    },
                    "required": ["image_path", "template_path"]
                }
            })
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用，符合MCP协议标准
        """
        try:
            if name == "list_directory":
                path = arguments.get("path")
                if not path or not os.path.isdir(path):
                    return {"status": "error", "error": "Invalid or missing path"}
                items = os.listdir(path)
                return {"status": "success", "items": items}
            elif name == "read_file":
                path = arguments.get("path")
                if not path or not os.path.isfile(path):
                    return {"status": "error", "error": "Invalid or missing file path"}
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"status": "success", "content": content}
            elif name == "start_process":
                command = arguments.get("command")
                if not command:
                    return {"status": "error", "error": "Missing command"}
                import subprocess
                process = subprocess.Popen(command, shell=True)
                return {"status": "success", "pid": process.pid}
            elif name == "execute_shell":
                command = arguments.get("command")
                if not command:
                    return {"status": "error", "error": "Missing command"}
                import subprocess
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()
                return {
                    "status": "success" if process.returncode == 0 else "error",
                    "returncode": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr
                }
            elif name == "mouse_click":
                from tools.mouse_keyboard_tool import MouseKeyboardTool
                mk_tool = MouseKeyboardTool()
                x = arguments.get("x", 0)
                y = arguments.get("y", 0)
                button = arguments.get("button")
                mk_tool.move_mouse(x, y)
                return mk_tool.mouse_click(button)
            elif name == "move_mouse":
                from tools.mouse_keyboard_tool import MouseKeyboardTool
                mk_tool = MouseKeyboardTool()
                x = arguments.get("x", 0)
                y = arguments.get("y", 0)
                return mk_tool.move_mouse(x, y)
            elif name == "key_press":
                from tools.mouse_keyboard_tool import MouseKeyboardTool
                mk_tool = MouseKeyboardTool()
                key = arguments.get("key", "")
                key_map = {
                    "W": 0x57, "A": 0x41, "S": 0x53, "D": 0x44, "ENTER": 0x0D, "SPACE": 0x20
                }
                key_code = key_map.get(key.upper(), ord(key.upper()) if len(key) == 1 else 0)
                return mk_tool.key_press(key_code)
            elif name == "sleep":
                # 兼容同步和异步调用
                ms = arguments.get("ms")
                s = arguments.get("s")
                coro = sleep_tool(ms=ms, s=s)
                if asyncio.iscoroutine(coro):
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(coro)
                else:
                    return coro
            elif name == "ocr":
                from tools.ocr_tool import OCRFactory
                image_path = arguments.get("image_path")
                backend = arguments.get("backend", "easyocr")
                lang = arguments.get("lang")
                detailed = arguments.get("detailed", False)
                if not image_path:
                    return {"status": "error", "error": "缺少图片路径"}
                # 路径修正：相对路径转绝对路径
                if not os.path.isabs(image_path):
                    image_path = os.path.abspath(image_path)
                try:
                    from common.json_utils import dumps, loads
                    ocr = OCRFactory.create(backend, lang=lang)
                    result = ocr.recognize(image_path, lang=lang, detailed=detailed)
                    # 使用自定义JSON编码器处理可能包含numpy数据类型的结果
                    # 先序列化再反序列化，确保所有numpy类型都被转换为Python原生类型
                    result_serializable = loads(dumps(result))
                    if detailed:
                        return {"status": "success", "result": result_serializable}
                    else:
                        return {"status": "success", "text": result_serializable}
                except BaseException as e:
                    return {"status": "error", "error": str(e)}
            elif name == "screenshot":
                from tools.screenshot_tool import ScreenshotTool
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
            elif name == "find_text_pos":
                from tools.image_finder_tool import ImageFinderTool
                # 文找坐标功能
                text = arguments.get("text")
                image_path = arguments.get("image_path")
                threshold = arguments.get("threshold", 0.7)
                ocr_backend = arguments.get("ocr_backend", "easyocr")
                lang = arguments.get("lang")
                if not text or not image_path:
                    return {"status": "error", "error": "缺少必要参数text或image_path"}
                try:
                    pos_tool = ImageFinderTool(ocr_backend=ocr_backend, lang=lang)
                    result = pos_tool.find_text(image_path, text, threshold)
                    return {"status": "success", "result": result}
                except BaseException as e:
                    return {"status": "error", "error": str(e)}
            elif name == "find_image_pos":
                from tools.image_finder_tool import ImageFinderTool
                # 图找坐标功能
                template_path = arguments.get("template_path")
                image_path = arguments.get("image_path")
                threshold = arguments.get("threshold", 0.7)
                ocr_backend = arguments.get("ocr_backend", "easyocr")
                lang = arguments.get("lang")
                if not template_path or not image_path:
                    return {"status": "error", "error": "缺少必要参数template_path或image_path"}
                try:
                    pos_tool = ImageFinderTool(ocr_backend=ocr_backend, lang=lang)
                    result = pos_tool.find_image(image_path, template_path, threshold)
                    return {"status": "success", "result": result}
                except BaseException as e:
                    return {"status": "error", "error": str(e)}
            
            else:
                return {"status": "error", "error": f"Unknown tool: {name}"}
        except BaseException as e:
            return {"status": "error", "error": str(e)}