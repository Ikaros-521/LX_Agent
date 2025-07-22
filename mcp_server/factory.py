# MCP工厂类实现

from typing import Dict, Any, Optional
import importlib
from loguru import logger

from mcp_server.base import BaseMCP
from mcp_server.local_mcp import LocalMCPAdapter
from mcp_server.async_cloud_mcp import AsyncCloudMCPAdapter


class MCPFactory:
    """
    MCP工厂类，用于创建不同类型的MCP适配器
    """
    
    @staticmethod
    def create(name: str, config: Dict[str, Any]) -> Optional[BaseMCP]:
        """
        创建MCP适配器实例
        
        Args:
            name: MCP名称
            config: MCP配置信息
            
        Returns:
            Optional[BaseMCP]: MCP适配器实例，如果创建失败则返回None
        """
        mcp_type = config.get("type", "")
        
        if not mcp_type:
            logger.error(f"MCP type not specified for {name}")
            return None
        
        try:
            # 根据类型创建对应的MCP适配器
            if mcp_type == "local":
                return LocalMCPAdapter(config)
            elif mcp_type == "cloud":
                return AsyncCloudMCPAdapter(config)
            else:
                # 尝试动态加载自定义MCP适配器
                module_path = config.get("module", "")
                class_name = config.get("class", "")
                
                if not module_path or not class_name:
                    logger.error(f"Module path or class name not specified for custom MCP {name}")
                    return None
                
                try:
                    module = importlib.import_module(module_path)
                    mcp_class = getattr(module, class_name)
                    return mcp_class(config)
                except (ImportError, AttributeError) as e:
                    logger.error(f"Failed to load custom MCP {name}: {str(e)}")
                    return None
        except BaseException as e:
            logger.error(f"Failed to create MCP {name}: {str(e)}")
            return None