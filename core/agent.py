# Agent类实现

from loguru import logger
from typing import Dict, Any, List, Optional
import platform

from config import Config
from mcp.router import MCPRouter
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
    
    def initialize(self) -> bool:
        """
        初始化Agent
        
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            return True
            
        # 初始化MCP路由器
        if not self.mcp_router.initialize():
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
    
    def execute(self, command: str, required_capabilities: List[str] = None) -> Dict[str, Any]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            required_capabilities: 所需的能力列表，默认为None
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        if not self.initialized:
            if not self.initialize():
                return {
                    "status": "error",
                    "error": "Agent not initialized"
                }
        
        # 执行命令
        return self.mcp_router.execute_command(command, required_capabilities)
    
    def analyze_command(self, command: str) -> List[str]:
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
    
    def execute_with_analysis(self, command: str, history: list = None) -> Dict[str, Any]:
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
            tool_calls = self.llm.analyze_and_generate_tool_calls(command, all_tools, os_type=os_type, history=history)
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
            result = self.mcp_router.execute_tool_call(name, arguments)
            results.append({"tool": name, "result": result})
        return {"status": "success", "results": results}
    
    def summarize_result(self, command: str, result: Dict[str, Any]) -> str:
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
    
    def close(self) -> None:
        """
        关闭Agent
        """
        if self.initialized:
            self.mcp_router.close()
            self.initialized = False