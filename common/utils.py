# 通用工具函数

import os
import sys
import platform
import subprocess
from loguru import logger
from typing import Dict, Any, List, Optional, Tuple



def is_windows() -> bool:
    """
    检查当前系统是否为Windows
    
    Returns:
        bool: 是否为Windows系统
    """
    return platform.system() == "Windows"

def is_linux() -> bool:
    """
    检查当前系统是否为Linux
    
    Returns:
        bool: 是否为Linux系统
    """
    return platform.system() == "Linux"

def is_macos() -> bool:
    """
    检查当前系统是否为macOS
    
    Returns:
        bool: 是否为macOS系统
    """
    return platform.system() == "Darwin"

def run_command(command: str, shell: bool = None, **kwargs) -> Tuple[int, str, str]:
    """
    运行命令
    
    Args:
        command: 要运行的命令
        shell: 是否使用shell运行，默认根据操作系统自动判断
        **kwargs: 其他参数
        
    Returns:
        Tuple[int, str, str]: 返回码、标准输出、标准错误
    """
    # 如果没有指定shell，根据操作系统自动判断
    if shell is None:
        shell = is_windows()
    
    try:
        # 运行命令
        process = subprocess.Popen(
            command,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs
        )
        
        # 获取输出
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        logger.error(f"Failed to run command: {str(e)}")
        return -1, "", str(e)

def ensure_dir(path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {str(e)}")
        return False

def is_path_allowed(path: str, allowed_paths: List[str], denied_paths: List[str]) -> bool:
    """
    检查路径是否被允许访问
    
    Args:
        path: 要检查的路径
        allowed_paths: 允许的路径列表
        denied_paths: 禁止的路径列表
        
    Returns:
        bool: 路径是否被允许访问
    """
    # 标准化路径
    path = os.path.abspath(path)
    
    # 检查是否在禁止的路径中
    for denied in denied_paths:
        denied = os.path.abspath(denied)
        if path.startswith(denied):
            return False
    
    # 检查是否在允许的路径中
    for allowed in allowed_paths:
        allowed = os.path.abspath(allowed)
        if path.startswith(allowed):
            return True
    
    # 默认不允许
    return False

def get_file_type(path: str) -> str:
    """
    获取文件类型
    
    Args:
        path: 文件路径
        
    Returns:
        str: 文件类型
    """
    if not os.path.exists(path):
        return "not_exist"
        
    if os.path.isdir(path):
        return "directory"
        
    if os.path.isfile(path):
        return "file"
        
    return "unknown"

def format_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
        
    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.2f} KB"
        
    size_mb = size_kb / 1024
    if size_mb < 1024:
        return f"{size_mb:.2f} MB"
        
    size_gb = size_mb / 1024
    return f"{size_gb:.2f} GB"

def build_capabilities_prompt(capabilities_detail):
    """
    根据MCP能力详情生成能力描述字符串
    """
    abilities_str = ""
    if capabilities_detail:
        tool_names = set()
        for mcp in capabilities_detail:
            tools = mcp.get("capabilities", {}).get("tools", {}).get("tools", [])
            for tool in tools:
                name = tool.get("name", "")
                desc = tool.get("description", "")
                params = tool.get("parameters", {})
                param_str = ""
                if params and params.get("properties"):
                    param_str = "，参数：" + ", ".join([f"{k}({v.get('description','')})" for k,v in params["properties"].items()])
                if name and name not in tool_names:
                    abilities_str += f"- {name}（{desc}{param_str}）\n"
                    tool_names.add(name)
    if not abilities_str:
        abilities_str = "- file（文件操作）\n- browser（浏览器操作）\n- mouse（鼠标操作）\n- keyboard（键盘操作）\n- process（进程操作）\n- shell（命令行操作）\n"
    return abilities_str