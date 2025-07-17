# 配置模块

import os
import yaml
from loguru import logger
from typing import Dict, Any, Optional



class Config:
    """
    配置管理类，用于加载和管理配置信息
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为None，将使用默认路径
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.yaml")
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}")
                return False
                
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
                
            logger.info(f"Config loaded from {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                
            logger.info(f"Config saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置项键名
            default: 默认值，如果配置项不存在则返回此值
            
        Returns:
            Any: 配置项值
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置项键名
            value: 配置项值
        """
        self.config[key] = value
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """
        获取MCP配置
        
        Returns:
            Dict[str, Any]: MCP配置
        """
        return self.config.get("mcp", {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        获取LLM配置
        
        Returns:
            Dict[str, Any]: LLM配置
        """
        return self.config.get("llm", {})
    
    def get_tools_config(self) -> Dict[str, Any]:
        """
        获取工具配置
        
        Returns:
            Dict[str, Any]: 工具配置
        """
        return self.config.get("tools", {})
    
    def get_logger_config(self) -> Dict[str, Any]:
        """
        获取日志配置
        
        Returns:
            Dict[str, Any]: 日志配置
        """
        return self.config.get("logging", {})
    
    def get_context_config(self) -> Dict[str, Any]:
        """
        获取对话上下文配置
        Returns:
            Dict[str, Any]: 上下文配置
        """
        return self.config.get("context", {})