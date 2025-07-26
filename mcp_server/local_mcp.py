# 本地MCP适配器实现

import subprocess
import platform
import os
import importlib
import pkgutil
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
        self.capabilities = set()
        self.tools_schema = []
        self.tool_modules = {}
        self.connected = False
        self.system = platform.system()
        self._load_tools()
    
    def _load_tools(self):
        """
        自动加载所有工具模块
        """
        try:
            import tools
            for _, modname, ispkg in pkgutil.iter_modules(tools.__path__):
                if modname.endswith("_tool"):
                    try:
                        module = importlib.import_module(f"tools.{modname}")
                        if hasattr(module, "get_capabilities"):
                            self.capabilities.update(module.get_capabilities())
                        if hasattr(module, "get_tools"):
                            for tool in module.get_tools():
                                self.tools_schema.append(tool)
                                self.tool_modules[tool["name"]] = module
                    except Exception as e:
                        print(f"Failed to load tool module {modname}: {e}")
        except Exception as e:
            print(f"Failed to load tools: {e}")
    
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
            "capabilities": list(self.capabilities)
        }
    
    async def get_capabilities(self) -> List[str]:
        """
        返回本地MCP支持的能力列表
        
        Returns:
            List[str]: 能力列表
        """
        return list(self.capabilities)
    
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
        return self.tools_schema
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用，符合MCP协议标准
        """
        try:
            module = self.tool_modules.get(name)
            if not module:
                return {"status": "error", "error": f"Unknown tool: {name}"}
            return module.call_tool(name, arguments)
        except BaseException as e:
            return {"status": "error", "error": str(e)}