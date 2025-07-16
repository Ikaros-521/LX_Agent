# Anthropic模型实现

import os
import logging
import requests
from typing import Dict, List, Any, Optional, Union

from .base import BaseLLM
from common.utils import build_capabilities_prompt

logger = logging.getLogger(__name__)

class AnthropicLLM(BaseLLM):
    """
    Anthropic大模型实现
    """
    
    def __init__(self, api_key: str = None, model: str = "claude-3-opus-20240229", **kwargs):
        """
        初始化Anthropic大模型
        
        Args:
            api_key: Anthropic API密钥，如果为None则尝试从环境变量获取
            model: 模型名称，默认为claude-3-opus-20240229
            **kwargs: 其他参数
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("Anthropic API key not provided and not found in environment variables")
            
        self.model = model
        self.default_params = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 1.0)
        }
        
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示文本
            **kwargs: 其他参数，如温度、最大token数等
            
        Returns:
            str: 生成的文本响应
        """
        try:
            # 合并默认参数和传入的参数
            params = {**self.default_params, **kwargs}
            
            # 准备请求头和请求体
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": params["temperature"],
                "max_tokens": params["max_tokens"],
                "top_p": params["top_p"]
            }
            
            # 发送请求
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            return result["content"][0]["text"]
        except Exception as e:
            logger.error(f"Error generating text with Anthropic: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_embeddings(self, text: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """
        获取文本的向量嵌入表示
        
        Args:
            text: 输入文本或文本列表
            **kwargs: 其他参数
            
        Returns:
            Union[List[float], List[List[float]]]: 文本的向量嵌入表示
        """
        # 注意：Anthropic目前没有官方的嵌入API，这里使用一个简单的实现
        # 在实际应用中，可以使用其他服务（如OpenAI）的嵌入API
        logger.warning("Anthropic does not provide an official embeddings API. Using a placeholder implementation.")
        
        # 返回一个简单的占位符实现
        if isinstance(text, str):
            return [0.0] * 1024  # 返回零向量，维度为1024
        return [[0.0] * 1024 for _ in range(len(text))]
    
    def analyze_command(self, command: str, capabilities_detail: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        分析命令所需的能力
        Args:
            command: 要分析的命令
            capabilities_detail: 所有MCP的详细能力信息
        Returns:
            List[str]: 所需的能力列表
        """
        try:
            abilities_str = build_capabilities_prompt(capabilities_detail)
            prompt = f"""
分析以下命令，并列出执行该命令所需的能力。可能的能力包括：\n{abilities_str}\n命令：{command}\n所需能力（仅返回能力名称，用逗号分隔）："""
            response = self.generate(prompt)
            capabilities = [cap.strip() for cap in response.split(",")]
            return capabilities
        except Exception as e:
            logger.error(f"Error analyzing command with Anthropic: {str(e)}")
            # 简单实现，根据关键词判断
            capabilities = []
            if any(kw in command.lower() for kw in ["file", "folder", "directory", "path", "open", "read", "write"]):
                capabilities.append("file")
            if any(kw in command.lower() for kw in ["browser", "web", "url", "http", "https"]):
                capabilities.append("browser")
            if any(kw in command.lower() for kw in ["process", "run", "execute", "start", "stop", "kill"]):
                capabilities.append("process")
            if any(kw in command.lower() for kw in ["mouse", "click", "move", "drag", "scroll"]):
                capabilities.append("mouse")
            if any(kw in command.lower() for kw in ["keyboard", "type", "key", "press", "input"]):
                capabilities.append("keyboard")
            return capabilities
    
    def summarize_result(self, command: str, result: Dict[str, Any]) -> str:
        """
        总结命令执行结果
        
        Args:
            command: 执行的命令
            result: 命令执行结果
            
        Returns:
            str: 总结文本
        """
        try:
            # 构建提示
            prompt = f"""总结以下命令的执行结果：

命令：{command}

执行结果：{result}

请用简洁明了的语言总结执行结果："""
            
            # 调用Anthropic API
            response = self.generate(prompt)
            
            return response
        except Exception as e:
            logger.error(f"Error summarizing result with Anthropic: {str(e)}")
            
            # 简单实现，直接返回状态和结果
            status = result.get("status", "unknown")
            if status == "success":
                return f"命令执行成功。{result.get('stdout', '')}"
            else:
                return f"命令执行失败。错误：{result.get('error', '未知错误')}"