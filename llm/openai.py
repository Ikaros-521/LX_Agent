# OpenAI模型实现

import os
from loguru import logger
import openai
from typing import Dict, List, Any, Optional, Union

from .base import BaseLLM
from common.utils import build_capabilities_prompt



class OpenAILLM(BaseLLM):
    """
    OpenAI大模型实现
    """
    
    def __init__(self, config: Dict[str, Any]):
        # 1. 首先调用父类的__init__方法，正确传递配置
        super().__init__(config)
        
        # 2. 初始化 OpenAI 客户端
        self.client = openai.OpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("base_url")
        )

        # 3. 恢复 self.model 属性，供 generate/generate_stream 方法使用
        self.model = config.get("model")

        # 4. 恢复 self.default_params 字典，并从 config 中读取参数
        self.default_params = {
            "temperature": config.get("temperature", 0.7),
            "max_tokens": self.max_tokens,  # 直接使用父类中已初始化的max_tokens
            "top_p": config.get("top_p", 1.0),
            "frequency_penalty": config.get("frequency_penalty", 0.0),
            "presence_penalty": config.get("presence_penalty", 0.0)
        }

        # 5. 增加超时机制，默认60秒
        self.timeout = config.get("timeout", 60)

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
            params = {**self.default_params, **kwargs}
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=params["temperature"],
                max_tokens=params["max_tokens"],
                top_p=params["top_p"],
                frequency_penalty=params["frequency_penalty"],
                presence_penalty=params["presence_penalty"],
                timeout=self.timeout
            )
            # logger.info(f"OpenAI返回需要调用的工具: {response.choices[0].message.content.strip()}")
            # 新版返回choices[0].message.content
            return response.choices[0].message.content.strip()
        except BaseException as e:
            logger.error(f"Error generating text with OpenAI: {str(e)} | prompt={prompt} | params={kwargs}", exc_info=True)
            return f"Error: {str(e)}"

    def generate_stream(self, prompt: str, **kwargs):
        """
        流式生成文本响应
        Yields:
            str: 生成的文本片段
        """
        params = {**self.default_params, **kwargs}
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=params["temperature"],
                max_tokens=params["max_tokens"],
                top_p=params["top_p"],
                frequency_penalty=params["frequency_penalty"],
                presence_penalty=params["presence_penalty"],
                stream=True,
                timeout=self.timeout
            )
            for chunk in response:
                delta = getattr(chunk.choices[0].delta, 'content', None)
                if delta:
                    yield delta
        except BaseException as e:
            logger.error(f"Error in OpenAI stream: {str(e)}")
            yield f"[OpenAI流式错误]: {str(e)}"

    def get_embeddings(self, text: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """
        获取文本的向量嵌入表示
        
        Args:
            text: 输入文本或文本列表
            **kwargs: 其他参数
        Returns:
            Union[List[float], List[List[float]]]: 文本的向量嵌入表示
        """
        try:
            if isinstance(text, str):
                texts = [text]
            else:
                texts = text
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts,
                timeout=self.timeout
            )
            # 新版返回data[i].embedding
            embeddings = [item.embedding for item in response.data]
            if isinstance(text, str):
                return embeddings[0]
            return embeddings
        except BaseException as e:
            logger.error(f"Error getting embeddings with OpenAI: {str(e)} | text={text}", exc_info=True)
            if isinstance(text, str):
                return [0.0] * 1536  # 返回零向量，维度为1536
            return [[0.0] * 1536 for _ in range(len(text))]

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
        except BaseException as e:
            logger.error(f"Error analyzing command with OpenAI: {str(e)} | command={command}", exc_info=True)
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

    

    def nl_to_shell_command(self, instruction: str, os_type: str = "Windows") -> str:
        """
        将自然语言指令转为具体的shell命令
        Args:
            instruction: 用户的自然语言指令
            os_type: 操作系统类型（Windows/Linux/Mac）
        Returns:
            str: 生成的shell命令
        """
        prompt = f"""你是一个命令行专家，请将下述用户需求转为{os_type}系统下可直接执行的shell命令，只返回命令本身，不要解释。\n\n用户需求：{instruction}\n命令："""
        return self.generate(prompt)
