# MCP适配层初始化文件

"""
MCP (Machine Control Protocol) 适配层

该模块提供了与不同MCP服务交互的接口和实现，包括：
- BaseMCP: MCP适配器的基础抽象接口
- LocalMCPAdapter: 本地MCP适配器实现
- CloudMCPAdapter: 云端MCP适配器实现
- MCPFactory: MCP适配器工厂类，用于创建不同类型的MCP适配器
- MCPRouter: MCP路由器，用于管理多个MCP服务和路由策略
"""

from .base import BaseMCP
from .local_mcp import LocalMCPAdapter
from .cloud_mcp import CloudMCPAdapter
from .factory import MCPFactory
from .router import MCPRouter

__all__ = [
    'BaseMCP',
    'LocalMCPAdapter',
    'CloudMCPAdapter',
    'MCPFactory',
    'MCPRouter'
]