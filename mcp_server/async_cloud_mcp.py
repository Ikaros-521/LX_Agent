from mcp.client.streamable_http import streamablehttp_client
from loguru import logger
from typing import Any, List, Dict
import asyncio


class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict,
        title: str | None = None,
    ) -> None:
        self.name: str = name
        self.title: str | None = title
        self.description: str = description
        self.inputSchema: dict = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM.

        Returns:
            A formatted string describing the tool.
        """
        args_desc = []
        if "properties" in self.inputSchema:
            for param_name, param_info in self.inputSchema["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.inputSchema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        # Build the formatted output with title as a separate field
        output = f"Tool: {self.name}\n"

        # Add human-readable title if available
        if self.title:
            output += f"User-readable title: {self.title}\n"

        output += f"""Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""

        return output

class AsyncCloudMCPAdapter:
    def __init__(self, config):
        if isinstance(config, dict):
            self.config = config
            self.url = config.get("url")
            self.api_key = config.get("api_key")
            self.timeout = config.get("timeout", 30)
            self.capabilities = []
        else:
            self.config = None
            self.url = config
            self.api_key = None
            self.timeout = 30
            self.capabilities = []
        self.session = None
        self._client_ctx = None
        self._client = None
        self._session_ctx = None

    async def connect(self):
        import mcp  # 避免循环依赖
        self._client_ctx = streamablehttp_client(self.url)
        self._client = await self._client_ctx.__aenter__()
        read_stream, write_stream, _ = self._client
        self._session_ctx = mcp.ClientSession(read_stream, write_stream)
        self.session = await self._session_ctx.__aenter__()
        await self.session.initialize()
        try:
            self.capabilities = await self.get_capabilities()
        except Exception as e:
            logger.error(f"Error fetching capabilities: {e}")
            self.capabilities = []

    async def disconnect(self):
        if self.session and self._session_ctx:
            await self._session_ctx.__aexit__(None, None, None)
            self.session = None
            self._session_ctx = None
        if self._client_ctx:
            await self._client_ctx.__aexit__(None, None, None)
            self._client_ctx = None
            self._client = None

    async def is_available(self):
        return self.session is not None

    async def _get_tools(self) -> List[Tool]:
        if not self.session:
            raise RuntimeError("Not connected")
        tools_response = await self.session.list_tools()
        tools = []
        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                tools.extend(
                    Tool(tool.name, tool.description, tool.inputSchema, getattr(tool, "title", None))
                    for tool in item[1]
                )
        return tools

    async def list_tools(self) -> List[Dict[str, Any]]:
        """返回 List[dict]，每个 dict 包含工具详细信息，便于主流程聚合"""
        try:
            tools = await self._get_tools()
            return [
                {
                    "name": tool.name,
                    "title": tool.title,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                }
                for tool in tools
            ]
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []

    async def call_tool(self, name, arguments, retries=2, delay=1.0):
        if not self.session:
            raise RuntimeError("Not connected")
        attempt = 0
        while attempt < retries:
            try:
                return await self.session.call_tool(name, arguments)
            except Exception as e:
                attempt += 1
                logger.warning(f"Error executing tool: {e}. Attempt {attempt} of {retries}.")
                if attempt < retries:
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries reached. Failing.")
                    raise

    async def get_capabilities(self) -> List[str]:
        """返回所有工具名列表"""
        try:
            tools = await self._get_tools()
            return [tool.name for tool in tools]
        except Exception as e:
            logger.error(f"Error getting capabilities: {e}")
            return []
    