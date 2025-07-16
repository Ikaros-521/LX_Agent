# 本地MCP适配器实现

import subprocess
import platform
import os
from typing import Dict, Any, List, Optional

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
    
    def get_capabilities_detail(self) -> Dict[str, Any]:
        """
        返回本地MCP支持的详细能力描述，结构参考标准MCP协议。
        """
        # 这里只做简单示例，真实可扩展为自动发现本地工具
        tools = []
        if "file" in self.capabilities:
            tools.append({
                "name": "file",
                "description": "文件操作，如读取、写入、列目录等",
                "parameters": {"type": "object", "properties": {}, "required": []}
            })
        if "process" in self.capabilities:
            tools.append({
                "name": "process",
                "description": "进程操作，如启动、终止进程等",
                "parameters": {"type": "object", "properties": {}, "required": []}
            })
        if "shell" in self.capabilities:
            tools.append({
                "name": "shell",
                "description": "执行Shell命令",
                "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "要执行的命令"}}, "required": ["command"]}
            })
        if "mouse_keyboard" in self.capabilities:
            tools.append({
                "name": "mouse_keyboard",
                "description": "鼠标键盘操作，如移动鼠标、点击、按下键盘等",
                "parameters": {"type": "object", "properties": {}, "required": []}
            })
        # 可扩展其它能力
        return {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {
                    "listChanged": True,
                    "tools": tools
                },
                "prompts": {
                    "listChanged": False,
                    "prompts": []
                }
            },
            "serverInfo": {
                "name": "local-mcp",
                "version": "1.0.0"
            }
        }
    
    def is_available(self) -> bool:
        """
        检查本地MCP是否可用
        
        Returns:
            bool: MCP是否可用
        """
        return self.connected