# MCP抽象接口定义

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseMCP(ABC):
    """
    MCP服务抽象基类，所有MCP适配器都需要继承此类并实现其方法
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接到MCP服务
        
        Returns:
            bool: 连接是否成功
        """
        pass
        
    @abstractmethod
    def disconnect(self) -> None:
        """
        断开MCP连接
        """
        pass
        
    @abstractmethod
    def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            **kwargs: 命令参数
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        pass
        
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        获取MCP状态
        
        Returns:
            Dict[str, Any]: MCP状态信息
        """
        pass
        
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        返回该MCP支持的能力列表
        
        Returns:
            List[str]: 能力列表，如['file', 'browser', 'mouse', 'process']
        """
        pass
        
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查MCP是否可用
        
        Returns:
            bool: MCP是否可用
        """
        pass

    @abstractmethod
    def tools_list(self) -> Dict[str, Any]:
        """
        返回该MCP支持的工具列表，符合MCP协议标准
        Returns:
            Dict[str, Any]: 工具列表，包含工具名称、描述、输入schema等
        """
        pass
        
    @abstractmethod
    def tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用，符合MCP协议标准
        Args:
            name: 工具名称
            arguments: 工具参数
        Returns:
            Dict[str, Any]: 工具执行结果
        """
        pass