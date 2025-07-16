# 核心层初始化文件

"""
核心层模块

该模块提供了LX_Agent的核心功能组件：
- Agent: 核心代理类，负责协调LLM和MCP，执行命令
"""

from .agent import Agent

__all__ = ['Agent']