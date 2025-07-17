# LLM基础抽象类

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import json
from loguru import logger
import re
import sys

class BaseLLM(ABC):
    """
    大型语言模型基础抽象类，定义了所有LLM实现必须遵循的接口
    """
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示文本
            **kwargs: 其他参数，如温度、最大token数等
            
        Returns:
            str: 生成的文本响应
        """
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs):
        """
        流式生成文本响应
        Yields:
            str: 生成的文本片段
        """
        pass
    
    @abstractmethod
    def get_embeddings(self, text: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """
        获取文本的向量嵌入表示
        
        Args:
            text: 输入文本或文本列表
            **kwargs: 其他参数
            
        Returns:
            Union[List[float], List[List[float]]]: 文本的向量嵌入表示
        """
        pass
    
    @abstractmethod
    def analyze_command(self, command: str) -> List[str]:
        """
        分析命令所需的能力
        
        Args:
            command: 要分析的命令
            
        Returns:
            List[str]: 所需的能力列表
        """
        pass
    
    @abstractmethod
    def summarize_result(self, command: str, result: Dict[str, Any]) -> str:
        """
        总结命令执行结果
        
        Args:
            command: 执行的命令
            result: 命令执行结果
            
        Returns:
            str: 总结文本
        """
        pass

    def analyze_and_generate_tool_calls(self, command: str, available_tools: List[Dict[str, Any]], os_type: str = None, history: list = None, stream: bool = False, on_delta=None) -> List[Dict[str, Any]]:
        """
        通用：分析用户命令并生成工具调用列表
        os_type: 操作系统类型（如 Windows、Linux、Darwin）
        history: 对话历史
        stream: 是否流式响应
        on_delta: 流式回调函数，每收到一段内容就调用一次
        """
        def parse_llm_json_response(response: str):
            # 1. 提取 markdown 代码块中的内容
            match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", response)
            if match:
                response = match.group(1)
            # 2. 去除前后空白
            response = response.strip()
            # 3. 尝试解析
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                try:
                    import ast
                    return ast.literal_eval(response)
                except Exception:
                    return []
        try:
            tools_info = []
            for tool in available_tools:
                tools_info.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "inputSchema": tool.get("inputSchema", {})
                })
            os_info = f"当前操作系统为：{os_type}。" if os_type else ""
            history_str = ""
            if history:
                history_str = "\n\n对话历史：\n" + "\n".join([f"用户: {h.get('command', '')}" for h in history])
            prompt = (
                f"{os_info}\n"
                f"分析用户需求并生成工具调用，如需存储数据，均存储到当前路径的tmp文件夹即可。可用工具：{tools_info}\n"
                f"{history_str}"
                f"\n用户需求：{command}\n\n"
                "请生成JSON格式的工具调用列表，例如：\n"
                "[\n"
                "  {\"name\": \"mouse_click\", \"arguments\": {\"x\": 300, \"y\": 300, \"button\": \"left\"}},\n"
                "  {\"name\": \"key_press\", \"arguments\": {\"key\": \"W\"}}\n"
                "]\n\n工具调用："
            )
            if stream:
                if on_delta is None:
                    def on_delta(delta):
                        print(delta, end='', flush=True)
                        sys.stdout.flush()
                chunks = []
                for delta in self.generate_stream(prompt):
                    if on_delta:
                        on_delta(delta)
                    chunks.append(delta)
                response = ''.join(chunks)
            else:
                response = self.generate(prompt)
                logger.info(f"LLM返回工具调用: {response}")
            print("")
            return parse_llm_json_response(response)
        except Exception as e:
            logger.error(f"Error generating tool calls: {str(e)}")
            return []