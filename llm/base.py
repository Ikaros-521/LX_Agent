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
    
    def intermediate_summary(self, command: str, history: list, stream: bool = False, on_delta=None) -> str:
        """
        中间总结：描述当前进展、遇到的问题、下一步建议
        支持流式响应
        """
        prompt = (
            f"你是一个任务执行智能体，以下是用户需求：{command}\n"
            f"到目前为止的执行历史：{history}\n"
            "请用简洁明了的语言总结当前进展、遇到的问题，并给出下一步建议。"
        )
        try:
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
                return ''.join(chunks)
            else:
                return self.generate(prompt)
        except Exception as e:
            logger.error(f"Error in intermediate_summary: {str(e)}")
            return "[中间总结失败]"

    def final_summary(self, command: str, history: list, stream: bool = False, on_delta=None) -> str:
        """
        最终总结：整体回顾、结果归纳、建议
        支持流式响应
        """
        prompt = (
            f"你是一个任务执行智能体，以下是用户需求：{command}\n"
            f"完整执行历史：{history}\n"
            "请用简洁明了的语言总结本次任务的整体过程、最终结果，并给出改进建议。"
        )
        try:
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
                return ''.join(chunks)
            else:
                return self.generate(prompt)
        except Exception as e:
            logger.error(f"Error in final_summary: {str(e)}")
            return "[最终总结失败]"

    def summarize_result(self, command: str, result: Dict[str, Any], stream: bool = False, on_delta=None) -> str:
        """
        总结命令执行结果（最终总结，兼容旧接口）
        支持流式响应
        """
        # 兼容历史，result 里一般有 'results' 字段
        history = result.get('results', result)
        return self.final_summary(command, history, stream=stream, on_delta=on_delta)

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
                f"分析用户需求并结合历史执行情况，生成当前情况下下一步需要调用的工具（只输出一个，或如果无需继续则返回空列表[]）。如需存储数据，均存储到当前路径的tmp文件夹即可。可用工具：{tools_info}\n"
                f"{history_str}"
                f"\n用户需求：{command}\n\n"
                "请生成JSON格式的工具调用列表，例如：\n"
                "[\n"
                "  {\"name\": \"mouse_click\", \"arguments\": {\"x\": 300, \"y\": 300, \"button\": \"left\"}}\n"
                "]\n"
                "如果你认为所有需求都已完成，不要再生成工具调用，直接返回空列表 []。\n"
                "\n工具调用："
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