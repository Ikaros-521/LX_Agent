# Agent类实现

from loguru import logger
from typing import Dict, Any, List, Optional

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
                capabilities_detail = self.mcp_router.get_all_capabilities_detail()
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
    
    def execute_with_analysis(self, command: str) -> Dict[str, Any]:
        """
        分析命令并执行
        
        Args:
            command: 要执行的命令
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 分析命令所需的能力
        required_capabilities = self.analyze_command(command)
        logger.info(f"需要的能力: {required_capabilities}")

        # 如果需要shell能力，先用LLM将自然语言转为shell命令
        if self.llm and "shell" in required_capabilities:
            # 判断操作系统类型
            import platform
            os_type = platform.system()
            if os_type == "Windows":
                os_type_str = "Windows"
            elif os_type == "Linux":
                os_type_str = "Linux"
            elif os_type == "Darwin":
                os_type_str = "Mac"
            else:
                os_type_str = os_type
            shell_cmd = self.llm.nl_to_shell_command(command, os_type=os_type_str)
            # 检查是否需要二次确认
            shell_confirm = self.config.config.get("security", {}).get("shell_confirm", True)
            if shell_confirm:
                return {
                    "status": "need_confirm",
                    "shell_cmd": shell_cmd,
                    "original_command": command,
                    "message": f"即将执行的Shell命令：{shell_cmd}\n请确认是否执行？（输入“确认”或“yes”或“y”执行，其他任意内容取消）"
                }
            else:
                return self.execute(shell_cmd, required_capabilities)
        else:
            # 其它情况保持原有逻辑
            return self.execute(command, required_capabilities)
    
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