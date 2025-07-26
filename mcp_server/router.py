# MCP路由器实现

from loguru import logger
from typing import Dict, Any, List, Optional, Tuple
import random
import inspect

from mcp_server.base import BaseMCP
from mcp_server.factory import MCPFactory



class MCPRouter:
    """
    MCP路由器，用于管理多个MCP服务和路由策略
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MCP路由器
        
        Args:
            config: 配置信息，包含MCP服务配置
        """
        self.config = config
        self.mcps: Dict[str, BaseMCP] = {}
        self.routing_strategy = config.get("routing_strategy", "capability_match")
        self.initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化所有MCP服务
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            return True
        mcp_config = self.config.get("mcp", {})
        services = mcp_config.get("services", {})
        for name, service_config in services.items():
            if not service_config.get("enabled", True):
                logger.info(f"MCP service {name} is disabled, skipping")
                continue
            mcp = MCPFactory.create(name, service_config)
            if not mcp:
                logger.error(f"Failed to create MCP service {name}")
                continue
            try:
                connect_method = mcp.connect

                try:
                    await connect_method()
                    self.mcps[name] = mcp
                    logger.info(f"MCP service {name} connected successfully")
                except BaseException as e:
                    logger.error(f"Error connecting to MCP service {name}: {str(e)}，已跳过")
                    continue
            except BaseException as e:
                logger.error(f"Error connecting to MCP service {name}: {str(e)}，已跳过")
                continue
        self.initialized = len(self.mcps) > 0
        return self.initialized
    
    async def get_available_mcps(self) -> List[Tuple[str, BaseMCP]]:
        """
        获取所有可用的MCP服务
        Returns:
            List[Tuple[str, BaseMCP]]: 可用的MCP服务列表，每个元素为(名称, MCP实例)元组
        """
        available = []
        for name, mcp in self.mcps.items():
            if await mcp.is_available():
                available.append((name, mcp))
        return available
    
    async def select_mcp_by_capability(self, required_capabilities: List[str]) -> Optional[Tuple[str, BaseMCP]]:
        """
        根据所需能力选择合适的MCP服务
        
        Args:
            required_capabilities: 所需的能力列表
            
        Returns:
            Optional[Tuple[str, BaseMCP]]: 选中的MCP服务，如果没有合适的则返回None
        """
        available_mcps = await self.get_available_mcps()
        if not available_mcps:
            return None
            
        # 如果没有指定所需能力，返回任意一个可用的MCP
        if not required_capabilities:
            return available_mcps[0]
            
        # 按优先级排序MCP服务
        sorted_mcps = sorted(
            available_mcps,
            key=lambda x: self.config.get("mcp", {}).get("services", {}).get(x[0], {}).get("priority", 0),
            reverse=True
        )
        
        # 找到能够满足所有所需能力的MCP
        for name, mcp in sorted_mcps:
            mcp_capabilities = await mcp.get_capabilities()
            if all(cap in mcp_capabilities for cap in required_capabilities):
                return name, mcp
                
        # 如果没有找到完全匹配的，返回能力最匹配的MCP
        best_match = None
        best_match_count = -1
        
        for name, mcp in sorted_mcps:
            mcp_capabilities = await mcp.get_capabilities()
            match_count = sum(1 for cap in required_capabilities if cap in mcp_capabilities)
            
            if match_count > best_match_count:
                best_match = (name, mcp)
                best_match_count = match_count
                
        return best_match
    
    async def select_mcp_by_priority(self) -> Optional[Tuple[str, BaseMCP]]:
        """
        根据优先级选择MCP服务
        
        Returns:
            Optional[Tuple[str, BaseMCP]]: 选中的MCP服务，如果没有可用的则返回None
        """
        available_mcps = await self.get_available_mcps()
        if not available_mcps:
            return None
            
        # 按优先级排序MCP服务
        sorted_mcps = sorted(
            available_mcps,
            key=lambda x: self.config.get("mcp", {}).get("services", {}).get(x[0], {}).get("priority", 0),
            reverse=True
        )
        
        return sorted_mcps[0] if sorted_mcps else None
    
    async def select_mcp_by_load_balance(self) -> Optional[Tuple[str, BaseMCP]]:
        """
        使用负载均衡策略选择MCP服务
        
        Returns:
            Optional[Tuple[str, BaseMCP]]: 选中的MCP服务，如果没有可用的则返回None
        """
        available_mcps = await self.get_available_mcps()
        if not available_mcps:
            return None
            
        # 随机选择一个可用的MCP
        return random.choice(available_mcps)
    
    async def select_mcp(self, required_capabilities: List[str] = None) -> Optional[Tuple[str, BaseMCP]]:
        """
        根据路由策略选择合适的MCP服务
        
        Args:
            required_capabilities: 所需的能力列表，默认为None
            
        Returns:
            Optional[Tuple[str, BaseMCP]]: 选中的MCP服务，如果没有合适的则返回None
        """
        if not self.initialized:
            if not await self.initialize():
                return None
                
        if not required_capabilities:
            required_capabilities = []
            
        # 根据路由策略选择MCP
        if self.routing_strategy == "capability_match":
            return await self.select_mcp_by_capability(required_capabilities)
        elif self.routing_strategy == "priority_first":
            return await self.select_mcp_by_priority()
        elif self.routing_strategy == "load_balance":
            return await self.select_mcp_by_load_balance()
        else:
            # 默认使用能力匹配策略
            return await self.select_mcp_by_capability(required_capabilities)
    
    async def execute_command(self, command: str, required_capabilities: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        执行命令，自动选择合适的MCP服务
        
        Args:
            command: 要执行的命令
            required_capabilities: 所需的能力列表，默认为None
            **kwargs: 命令参数
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 检查是否需要对shell命令二次确认
        shell_confirm = self.config.get("security", {}).get("shell_confirm", True)
        if required_capabilities and "shell" in required_capabilities and shell_confirm:
            print(f"[安全提示] 即将执行Shell命令：{command}\n请确认是否执行？（输入“确认”或“yes”执行，其他任意内容取消）")
            confirm = input("> ").strip().lower()
            if confirm not in ("确认", "yes", "y"):
                print("已取消执行。"); return {"status": "cancelled", "error": "用户取消了shell命令执行"}
        # 选择合适的MCP
        selected = await self.select_mcp(required_capabilities)
        if not selected:
            return {
                "status": "error",
                "error": "No available MCP service"
            }
            
        name, mcp = selected
        
        try:
            # 执行命令
            result = await mcp.execute_command(command, **kwargs)
            result["mcp_name"] = name
            return result
        except BaseException as e:
            # 如果执行失败，尝试使用其他MCP
            logger.error(f"Failed to execute command with MCP {name}: {str(e)}")
            
            # 获取其他可用的MCP
            available_mcps = await self.get_available_mcps()
            other_mcps = [(n, m) for n, m in available_mcps if n != name]
            
            if not other_mcps:
                return {
                    "status": "error",
                    "error": f"Failed to execute command: {str(e)}",
                    "mcp_name": name
                }
                
            # 尝试使用其他MCP执行命令
            for other_name, other_mcp in other_mcps:
                try:
                    result = await other_mcp.execute_command(command, **kwargs)
                    result["mcp_name"] = other_name
                    result["fallback"] = True
                    return result
                except BaseException as other_e:
                    logger.error(f"Failed to execute command with fallback MCP {other_name}: {str(other_e)}")
            
            # 所有MCP都失败
            return {
                "status": "error",
                "error": f"All MCP services failed to execute command",
                "original_error": str(e),
                "mcp_name": name
            }
    
    async def close(self) -> None:
        """
        关闭所有MCP连接
        """
        for name, mcp in self.mcps.items():
            try:
                disconnect_method = mcp.disconnect
                import inspect
                if inspect.iscoroutinefunction(disconnect_method):
                    await disconnect_method()
                else:
                    disconnect_method()
                logger.info(f"MCP service {name} disconnected")
            except BaseException as e:
                logger.error(f"Error disconnecting MCP service {name}: {str(e)}")
        self.mcps.clear()
        self.initialized = False

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        聚合所有可用MCP的工具列表，供LLM分析使用
        Returns:
            List[Dict[str, Any]]: 所有工具的列表
        """
        all_tools = []
        for name, mcp in self.mcps.items():
            try:
                tools = await mcp.list_tools()
                for tool in tools:
                    tool = dict(tool)  # 确保是 dict
                    tool["mcp_name"] = name  # 标记工具来源
                    all_tools.append(tool)
            except BaseException as e:
                logger.warning(f"MCP {name} list_tools error: {e}")
        return all_tools

    async def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用，自动路由到对应的MCP
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        Returns:
            Dict[str, Any]: 执行结果
        """
        for name, mcp in self.mcps.items():
            try:
                tools = await mcp.list_tools()
                tool_names = [tool["name"] for tool in tools]
                if tool_name in tool_names:
                    result = await mcp.call_tool(tool_name, arguments)
                    
                    # 处理 CallToolResult 对象，转换为标准字典格式
                    if not isinstance(result, dict):
                        # 处理 CallToolResult 对象
                        if hasattr(result, 'isError') and not result.isError:
                            # 解析 content 字段，提取文本内容
                            content_text = ""
                            if hasattr(result, 'content') and result.content:
                                for block in result.content:
                                    if hasattr(block, 'type') and block.type == "text":
                                        content_text += block.text
                                    elif hasattr(block, 'text'):
                                        # 直接有 text 属性的情况
                                        content_text += block.text
                            
                            # 如果有 structuredContent，也包含进去
                            if hasattr(result, 'structuredContent') and result.structuredContent:
                                content_text += f"\n结构化内容: {result.structuredContent}"
                            
                            return {"status": "success", "result": content_text, "mcp_name": name}
                        else:
                            # 如果命令执行失败
                            error_content = ""
                            if hasattr(result, 'content') and result.content:
                                for block in result.content:
                                    if hasattr(block, 'type') and block.type == "text":
                                        error_content += block.text
                                    elif hasattr(block, 'text'):
                                        error_content += block.text
                            return {"status": "error", "result": error_content, "mcp_name": name}
                    else:
                        # 如果已经是字典格式，直接返回
                        result["mcp_name"] = name
                        return result
            except BaseException as e:
                logger.warning(f"MCP {name} call_tool error: {e}")
        return {"status": "error", "error": f"Tool {tool_name} not found"}