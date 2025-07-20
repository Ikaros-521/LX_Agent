# Agent类实现

from loguru import logger
from typing import Dict, Any, List, Optional
import platform

from config import Config
from mcp_server.router import MCPRouter
from llm.factory import LLMFactory
from llm.base import BaseLLM



class Agent:
    """
    Agent类，作为核心层的主要组件，负责协调LLM和MCP
    """
    
    def __init__(self, config: Config):
        """
        初始化Agent
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.mcp_router = MCPRouter(config.config)
        self.llm = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化Agent
        
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            return True
            
        # 初始化MCP路由器
        if not await self.mcp_router.initialize():
            logger.error("Failed to initialize MCP router")
            return False
            
        # 初始化LLM
        try:
            self.llm = LLMFactory.create_from_config(self.config.config)
            if not self.llm:
                logger.warning("Failed to initialize LLM, will use fallback methods")
        except Exception as e:
            logger.warning(f"Error initializing LLM: {str(e)}")
            logger.warning("Will use fallback methods for command analysis")
            
        self.initialized = True
        return True
    
    async def execute(self, command: str, required_capabilities: List[str] = None) -> Dict[str, Any]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            required_capabilities: 所需的能力列表，默认为None
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        if not self.initialized:
            if not await self.initialize():
                return {
                    "status": "error",
                    "error": "Agent not initialized"
                }
        
        # 执行命令
        return await self.mcp_router.execute_command(command, required_capabilities)
    
    async def analyze_command(self, command: str) -> List[str]:
        """
        分析命令所需的能力
        
        Args:
            command: 要分析的命令
            
        Returns:
            List[str]: 所需的能力列表
        """
        # 使用LLM分析命令所需的能力
        if self.llm:
            try:
                # 获取所有MCP能力详情
                capabilities_detail = self.mcp_router.get_all_tools()
                return self.llm.analyze_command(command, capabilities_detail)
            except Exception as e:
                logger.error(f"Error analyzing command with LLM: {str(e)}")
                logger.info("Falling back to keyword-based analysis")
        
        # 如果LLM不可用或分析失败，使用关键词判断
        logger.info("Using keyword-based command analysis")
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
    
    async def execute_with_analysis(self, command: str, history: list = None) -> Dict[str, Any]:
        """
        分析命令并执行
        
        Args:
            command: 要执行的命令
            history: 对话历史
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 获取所有可用工具
        all_tools = self.mcp_router.get_all_tools()
        
        os_type = platform.system()
        # 让LLM生成工具调用，传递操作系统类型和上下文
        if self.llm:
            logger.info(f"LLM分析命令: {command}")
            tool_calls = self.llm.analyze_and_generate_tool_calls(command, all_tools, os_type=os_type, history=history, stream=True)
        else:
            tool_calls = []
        logger.info(f"LLM生成的工具调用: {tool_calls}")
        # 检查危险工具
        security_config = self.config.get_security_config()
        dangerous_tools = security_config.get("dangerous_tools", ["execute_shell", "start_process"])
        need_confirm_calls = []
        for call in tool_calls:
            if call.get("name") in dangerous_tools and security_config.get("shell_confirm", True):
                need_confirm_calls.append(call)
        if need_confirm_calls:
            return {
                "status": "need_confirm",
                "message": f"检测到高危操作: {', '.join([c['name'] for c in need_confirm_calls])}，是否确认执行？",
                "dangerous_calls": need_confirm_calls,
                "all_calls": tool_calls
            }
        results = []
        for call in tool_calls:
            name = call.get("name")
            arguments = call.get("arguments", {})
            result = await self.mcp_router.execute_tool_call(name, arguments)
            results.append({"tool": name, "result": result})
        return {"status": "success", "results": results}
    
    async def summarize_result(self, command: str, result: Dict[str, Any]) -> str:
        """
        总结命令执行结果
        
        Args:
            command: 执行的命令
            result: 命令执行结果
            
        Returns:
            str: 总结文本
        """
        # 使用LLM总结结果
        if self.llm:
            try:
                return self.llm.summarize_result(command, result)
            except Exception as e:
                logger.error(f"Error summarizing result with LLM: {str(e)}")
                logger.info("Falling back to simple result summary")
        
        # 如果LLM不可用或总结失败，使用简单实现
        status = result.get("status", "unknown")
        if status == "success":
            return f"命令执行成功。{result.get('stdout', '')}"
        else:
            return f"命令执行失败。错误：{result.get('error', '未知错误')}"
    
    async def close(self) -> None:
        """
        关闭Agent
        """
        if self.initialized:
            await self.mcp_router.close()
            self.initialized = False

    async def execute_interactive(self, command: str, history: list = None, max_steps: int = 10, auto_continue: bool = False) -> Dict[str, Any]:
        """
        智能体多轮自适应主循环：每步 LLM 总结，用户可介入决策，支持自动继续。每步都基于最新history重新分析下一步。
        """
        if history is None:
            history = []
        all_tools = self.mcp_router.get_all_tools()
        os_type = platform.system()
        step = 0
        while step < max_steps:
            # 1. LLM生成下一个工具调用建议（只取一个）
            if self.llm:
                tool_calls = self.llm.analyze_and_generate_tool_calls(
                    command, all_tools, os_type=os_type, history=history, stream=True
                )
            else:
                tool_calls = []
            logger.warning(f"第{step+1}步 LLM生成的工具调用: {tool_calls}")
            if not tool_calls:
                logger.info("LLM未生成更多工具调用，终止。")
                # 最终总结
                final_summary = None
                if self.llm:
                    final_summary = self.llm.final_summary(
                        command, history, stream=True, on_delta=lambda delta: print(delta, end='', flush=True)
                    )
                    logger.info(f"最终总结: {final_summary}")
                    print(f"最终总结: {final_summary}", flush=True)
                return {"status": "success", "results": history, "final_summary": final_summary}
            call = tool_calls[0]  # 只取第一个建议
            name = call.get("name")
            arguments = call.get("arguments", {})
            # 2. 高危操作检测
            security_config = self.config.get_security_config()
            dangerous_tools = security_config.get("dangerous_tools", ["execute_shell", "start_process"])
            if name in dangerous_tools and security_config.get("shell_confirm", True):
                print(f"检测到高危操作: {name}，参数: {arguments}，是否确认执行？(yes/确认/y)：", flush=True)
                confirm = input().strip().lower()
                if confirm not in ("确认", "yes", "y"):
                    logger.info("用户取消高危操作")
                    history.append({"command": call, "result": {"status": "cancelled"}})
                    step += 1
                    continue
            # 3. 执行工具
            result = await self.mcp_router.execute_tool_call(name, arguments)
            logger.info(f"[{name}] 执行结果: {result}")
            print(f"[{name}] 执行结果: {result}", flush=True)
            # 4. 记录到history
            history.append({"command": call, "result": result})
            # 5. LLM中间总结
            summary = None
            if self.llm:
                summary = self.llm.intermediate_summary(
                    command, history, stream=True, on_delta=lambda delta: print(delta, end='', flush=True)
                )
                logger.info(f"中间总结: {summary}")
                print(f"中间总结: {summary}", flush=True)
            # 6. 用户介入决策或自动继续
            if not auto_continue:
                print("请输入操作: [Enter继续/c终止/e编辑/r重新规划]：", end='', flush=True)
                user_input = input().strip().lower()
            else:
                user_input = ''  # 自动继续
            if user_input in ("c", "exit", "stop"):
                print("用户选择终止流程。", flush=True)
                # 最终总结
                final_summary = None
                if self.llm:
                    final_summary = self.llm.final_summary(
                        command, history, stream=True, on_delta=lambda delta: print(delta, end='', flush=True)
                    )
                    logger.info(f"最终总结: {final_summary}")
                    print(f"最终总结: {final_summary}", flush=True)
                return {"status": "stopped", "results": history, "final_summary": final_summary}
            elif user_input in ("e", "edit"):
                new_cmd = input("请输入新的指令：").strip()
                command = new_cmd
                print("已更新指令，重新规划。", flush=True)
                # history 不清空，继续基于新指令和已有history
            elif user_input in ("r", "replan"):
                print("用户要求重新规划。", flush=True)
                # history 不清空，继续基于已有history重新分析
            # 其他情况默认继续
            step += 1
        # 保底最终总结
        final_summary = None
        if self.llm:
            final_summary = self.llm.final_summary(
                command, history, stream=True, on_delta=lambda delta: print(delta, end='', flush=True)
            )
            logger.info(f"最终总结: {final_summary}")
            print(f"最终总结: {final_summary}", flush=True)
        return {"status": "success", "results": history, "final_summary": final_summary}