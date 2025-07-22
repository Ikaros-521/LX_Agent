# LLM基础抽象类

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import json
from loguru import logger
import re
import sys
import tiktoken

# --- BEGIN TOKENIZER & CONTEXT MANAGEMENT ---
_tokenizer = None

def get_tokenizer():
    """获取全局共享的 tokenizer 实例。"""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = tiktoken.get_encoding("cl100k_base")
    return _tokenizer

def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量。"""
    if not text:
        return 0
    tokenizer = get_tokenizer()
    return len(tokenizer.encode(text))

def _truncate_long_strings(data: Any, max_len: int = 1000, notice: str = "[...内容过长,已被裁剪...]") -> Any:
    """
    递归地遍历字典或列表，并裁剪其中过长的字符串。
    """
    if isinstance(data, dict):
        return {k: _truncate_long_strings(v, max_len, notice) for k, v in data.items()}
    elif isinstance(data, list):
        return [_truncate_long_strings(v, max_len, notice) for v in data]
    elif isinstance(data, str) and len(data) > max_len:
        # 对超长字符串进行裁剪
        return data[:max_len] + notice
    else:
        return data
# --- END TOKENIZER & CONTEXT MANAGEMENT ---


class BaseLLM(ABC):
    """
    大型语言模型基础抽象类，定义了所有LLM实现必须遵循的接口
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model", "unknown")
        # 增加 max_tokens 配置，用于上下文管理
        self.max_tokens = config.get("max_tokens", 4096)  # 默认 4k

    def _truncate_history(self, history: List[Dict], max_tokens: int, reserved_tokens: int = 1000) -> (List[Dict], bool):
        """
        如果 history 过长，则从旧到新进行裁剪，确保最新的记录被优先保留。
        如果单条记录过大，会对该记录内部的字符串进行裁剪。
        - max_tokens: 模型总的 token 限制
        - reserved_tokens: 为 prompt 的其他部分和模型输出保留的 token
        """
        available_tokens = max_tokens - reserved_tokens
        
        # 1. 从后向前（从新到旧）遍历历史记录，找出能保留的记录范围
        tokens_count = 0
        keep_from_index = -1

        for i in range(len(history) - 1, -1, -1):
            item_str = json.dumps(history[i], ensure_ascii=False)
            item_tokens = estimate_tokens(item_str)
            
            if tokens_count + item_tokens <= available_tokens:
                tokens_count += item_tokens
                keep_from_index = i
            else:
                break

        # 2. 如果连最新的一条记录都放不下，则对其进行内部字符串裁剪
        if keep_from_index == -1:
            if not history:
                return [], False
            
            logger.warning("历史记录的最新一项已超过 token 限制，将对其内容进行裁剪。")
            latest_item = history[-1]
            
            # 尝试不同粒度的裁剪，直到满足要求
            for max_str_len in [2000, 1000, 500, 200, 100, 50, 20]:
                truncated_item = _truncate_long_strings(latest_item, max_len=max_str_len)
                if estimate_tokens(json.dumps(truncated_item, ensure_ascii=False)) <= available_tokens:
                    logger.warning(f"最新历史项已通过字符串裁剪至可接受大小。")
                    return [truncated_item], True
            
            logger.error("对最新历史项进行内容裁剪后仍然过大，历史将被清空。")
            return [], True

        # 3. 如果保留的记录范围不包含全部历史，则进行切片
        original_tokens = estimate_tokens(json.dumps(history, ensure_ascii=False))
        if keep_from_index > 0:
            logger.warning(f"历史记录过长 ({original_tokens} tokens)，将自动从旧到新进行裁剪。")
            truncated_history = history[keep_from_index:]
            final_tokens = estimate_tokens(json.dumps(truncated_history, ensure_ascii=False))
            logger.warning(f"历史记录已裁剪至 {final_tokens} tokens，保留了最新的 {len(truncated_history)} 条记录。")
            return truncated_history, True
        
        # 如果 keep_from_index 为 0，说明所有历史都可保留
        return history, False

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
        # 在生成 prompt 前，对 history进行裁剪
        truncated_history, was_truncated = self._truncate_history(history, self.max_tokens)
        if was_truncated:
            print("[系统提示] 部分历史记录因过长已被自动裁剪。", flush=True)

        prompt = (
            f"你是一个任务执行智能体，以下是用户需求：{command}\n"
            f"到目前为止的执行历史：{truncated_history}\n"
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
        except BaseException as e:
            logger.error(f"Error in intermediate_summary: {str(e)}")
            return "[中间总结失败]"

    def final_summary(self, command: str, history: list, stream: bool = False, on_delta=None) -> str:
        """
        最终总结：整体回顾、结果归纳、建议
        支持流式响应
        """
        # 在生成 prompt 前，对 history进行裁剪
        truncated_history, was_truncated = self._truncate_history(history, self.max_tokens)
        if was_truncated:
            print("[系统提示] 部分历史记录因过长已被自动裁剪。", flush=True)

        prompt = (
            f"你是一个任务执行智能体，以下是用户需求：{command}\n"
            f"完整执行历史：{truncated_history}\n"
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
        except BaseException as e:
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

    async def analyze_and_generate_tool_calls(self, command: str, available_tools: List[Dict[str, Any]], os_type: str = None, history: list = None, stream: bool = False, on_delta=None) -> List[Dict[str, Any]]:
        """
        通用：分析用户命令并生成工具调用列表
        os_type: 操作系统类型（如 Windows、Linux、Darwin）
        history: 对话历史
        stream: 是否流式响应
        on_delta: 流式回调函数，每收到一段内容就调用一次
        """
        # 在生成 prompt 前，对 history进行裁剪
        truncated_history, was_truncated = self._truncate_history(history, self.max_tokens)
        if was_truncated:
            print("[系统提示] 部分历史记录因过长已被自动裁剪。", flush=True)

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
                except BaseException:
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
            # 优化history结构化展开
            history_str = ""
            if truncated_history:
                steps = []
                for idx, h in enumerate(truncated_history):
                    step_lines = [f"第{idx+1}步："]
                    cmd = h.get('command', '')
                    if cmd:
                        step_lines.append(f"- LLM工具调用建议: {cmd}")
                    result = h.get('result', '')
                    if result:
                        step_lines.append(f"- 执行结果: {result}")
                    summary = h.get('summary', '')
                    if summary:
                        step_lines.append(f"- LLM中间总结: {summary}")
                    steps.append("\n".join(step_lines))
                history_str = "\n\n历史执行过程：\n" + "\n\n".join(steps)
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
                "\n请优先参考上一步LLM中间总结中的建议，避免重复错误。\n"
                "\n重要提示：避免重复无效的操作。如果一个操作已经成功执行，但任务没有进展，请尝试使用不同的工具或参数，而不是重复同一个操作。\n"
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
        except BaseException as e:
            logger.error(f"Error generating tool calls: {str(e)}")
            return []