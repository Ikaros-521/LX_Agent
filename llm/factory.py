# LLM工厂类

from loguru import logger
from typing import Dict, Any, Optional

from .base import BaseLLM
from .openai import OpenAILLM
from .anthropic import AnthropicLLM
from .local import LocalLLM



class LLMFactory:
    """
    LLM工厂类，用于创建不同类型的LLM实例
    """
    
    @staticmethod
    def create(config: Dict[str, Any]) -> Optional[BaseLLM]:
        """
        根据配置创建LLM实例
        
        Args:
            config: LLM配置
            
        Returns:
            Optional[BaseLLM]: LLM实例，如果创建失败则返回None
        """
        llm_type = config.get("type")
        
        if not llm_type:
            logger.error("LLM type not specified in config")
            return None
            
        try:
            if llm_type == "openai":
                return OpenAILLM(
                    base_url=config.get("base_url"),
                    api_key=config.get("api_key"),
                    model=config.get("model", "gpt-4"),
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 4096)
                )
            elif llm_type == "anthropic":
                return AnthropicLLM(
                    api_key=config.get("api_key"),
                    model=config.get("model", "claude-3-opus-20240229"),
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 4096)
                )
            elif llm_type == "local":
                return LocalLLM(
                    model_path=config.get("model_path"),
                    device=config.get("device", "cpu"),
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 4096)
                )
            else:
                logger.error(f"Unsupported LLM type: {llm_type}")
                return None
        except Exception as e:
            logger.error(f"Error creating LLM instance: {str(e)}")
            return None
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Optional[BaseLLM]:
        """
        从全局配置创建默认LLM实例
        
        Args:
            config: 全局配置
            
        Returns:
            Optional[BaseLLM]: LLM实例，如果创建失败则返回None
        """
        llm_config = config.get("llm", {})
        default_llm = llm_config.get("default")
        
        if not default_llm:
            logger.error("Default LLM not specified in config")
            return None
            
        services = llm_config.get("services", {})
        service_config = services.get(default_llm)
        
        if not service_config:
            logger.error(f"Config for default LLM '{default_llm}' not found")
            return None
            
        return LLMFactory.create(service_config)