# 本地模型实现

import os
import logging
from typing import Dict, List, Any, Optional, Union

from .base import BaseLLM
from common.utils import build_capabilities_prompt

logger = logging.getLogger(__name__)

class LocalLLM(BaseLLM):
    """
    本地大模型实现
    """
    
    def __init__(self, model_path: str, device: str = "cpu", **kwargs):
        """
        初始化本地大模型
        
        Args:
            model_path: 模型路径
            device: 设备，可选值为cpu或cuda，默认为cpu
            **kwargs: 其他参数
        """
        self.model_path = model_path
        self.device = device
        self.default_params = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 1.0)
        }
        
        # 模型实例
        self.model = None
        self.tokenizer = None
        
        # 加载模型
        self._load_model()
    
    def _load_model(self):
        """
        加载本地模型
        """
        try:
            # 这里使用条件导入，避免在不需要时导入大型依赖
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            logger.info(f"Loading model from {self.model_path}")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # 如果使用CPU，确保模型在CPU上
            if self.device == "cpu":
                self.model = self.model.to("cpu")
                
            logger.info("Model loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import required modules: {str(e)}")
            logger.error("Please install transformers and torch: pip install transformers torch")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示文本
            **kwargs: 其他参数，如温度、最大token数等
            
        Returns:
            str: 生成的文本响应
        """
        if self.model is None or self.tokenizer is None:
            logger.error("Model or tokenizer not loaded")
            return "Error: Model not loaded"
            
        try:
            # 合并默认参数和传入的参数
            params = {**self.default_params, **kwargs}
            
            # 编码输入
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = inputs.to(self.model.device)
            
            # 生成输出
            import torch
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_new_tokens=params["max_tokens"],
                    temperature=params["temperature"],
                    top_p=params["top_p"],
                    do_sample=True
                )
                
            # 解码输出
            output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除输入提示
            response = output_text[len(prompt):].strip()
            
            return response
        except Exception as e:
            logger.error(f"Error generating text with local model: {str(e)}")
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
        if self.model is None or self.tokenizer is None:
            logger.error("Model or tokenizer not loaded")
            if isinstance(text, str):
                return [0.0] * 768  # 返回零向量，维度为768
            return [[0.0] * 768 for _ in range(len(text))]
            
        try:
            # 确保文本是列表形式
            if isinstance(text, str):
                texts = [text]
            else:
                texts = text
                
            import torch
            import torch.nn.functional as F
            
            # 获取嵌入
            embeddings = []
            for t in texts:
                # 编码输入
                inputs = self.tokenizer(t, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = inputs.to(self.model.device)
                
                # 获取最后一层隐藏状态
                with torch.no_grad():
                    outputs = self.model(**inputs, output_hidden_states=True)
                    
                # 使用最后一层的[CLS]令牌的隐藏状态作为嵌入
                last_hidden_state = outputs.hidden_states[-1]
                cls_embedding = last_hidden_state[0, 0, :].cpu().numpy().tolist()
                embeddings.append(cls_embedding)
            
            # 如果输入是单个字符串，返回单个嵌入向量
            if isinstance(text, str):
                return embeddings[0]
            return embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings with local model: {str(e)}")
            if isinstance(text, str):
                return [0.0] * 768  # 返回零向量，维度为768
            return [[0.0] * 768 for _ in range(len(text))]
    
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
            logger.error(f"Error analyzing command with local model: {str(e)}")
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
            
            # 调用本地模型
            response = self.generate(prompt)
            
            return response
        except Exception as e:
            logger.error(f"Error summarizing result with local model: {str(e)}")
            
            # 简单实现，直接返回状态和结果
            status = result.get("status", "unknown")
            if status == "success":
                return f"命令执行成功。{result.get('stdout', '')}"
            else:
                return f"命令执行失败。错误：{result.get('error', '未知错误')}"