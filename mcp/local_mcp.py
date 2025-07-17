# 本地MCP适配器实现

import subprocess
import platform
import os
from typing import Dict, Any, List, Optional
import asyncio
from tools.sleep_tool import sleep_tool

from mcp.base import BaseMCP

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
    
    def connect(self) -> bool:
        """
        连接到本地MCP
        
        Returns:
            bool: 连接是否成功
        """
        # 本地MCP不需要实际连接，只需检查环境
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """
        断开本地MCP连接
        """
        self.connected = False
    
    def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
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
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
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
    
    def get_capabilities(self) -> List[str]:
        """
        返回本地MCP支持的能力列表
        
        Returns:
            List[str]: 能力列表
        """
        return self.capabilities
    
    def is_available(self) -> bool:
        """
        检查本地MCP是否可用
        
        Returns:
            bool: MCP是否可用
        """
        return self.connected

    def tools_list(self) -> Dict[str, Any]:
        """
        返回本地MCP支持的工具列表，符合MCP协议标准
        """
        tools = []
        if "list_directory" in self.capabilities:
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
        if "read_file" in self.capabilities:
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
        if "start_process" in self.capabilities:
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
        if "execute_shell" in self.capabilities:
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
        if "mouse_click" in self.capabilities:
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
        if "move_mouse" in self.capabilities:
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
        if "key_press" in self.capabilities:
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
        if "sleep" in self.capabilities:
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
        return {"tools": tools}
    
    def tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
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
            else:
                return {"status": "error", "error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}