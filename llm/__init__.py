# LLM接入层初始化文件

"""
LLM接入层模块

该模块提供了与大型语言模型交互的接口和实现：
- BaseLLM: 大模型基础抽象类
- OpenAILLM: OpenAI模型实现
- AnthropicLLM: Anthropic模型实现
- LocalLLM: 本地模型实现
- LLMFactory: 大模型工厂类，用于创建不同类型的大模型实例
"""

from .base import BaseLLM
from .openai import OpenAILLM
from .anthropic import AnthropicLLM
from .local import LocalLLM
from .factory import LLMFactory

__all__ = ['BaseLLM', 'OpenAILLM', 'AnthropicLLM', 'LocalLLM', 'LLMFactory']