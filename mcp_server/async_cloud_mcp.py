from mcp.client.streamable_http import streamablehttp_client

class AsyncCloudMCPAdapter:
    def __init__(self, config):
        if isinstance(config, dict):
            self.config = config
            self.url = config.get("url")
            self.api_key = config.get("api_key")
            self.timeout = config.get("timeout", 30)
            self.capabilities = []  # 初始化为空，完全依赖云端
        else:
            self.config = None
            self.url = config
            self.api_key = None
            self.timeout = 30
            self.capabilities = []
        self.session = None
        self.client = None

    async def connect(self):
        import mcp  # 避免循环依赖
        async with streamablehttp_client(self.url) as client:
            read_stream, write_stream, _ = client
            self.session = mcp.ClientSession(read_stream, write_stream)
            await self.session.initialize()
            # 自动获取能力
            try:
                tools_result = await self.session.list_tools()
                self.capabilities = [t.name for t in tools_result.tools]
            except Exception as e:
                self.capabilities = []
            self.client = client  # 可选保存

    async def disconnect(self):
        if self.session:
            await self.session.close()
        self.session = None
        self.client = None

    @property
    def is_available(self):
        return self.session is not None
        
    async def list_tools(self):
        if not self.session:
            raise RuntimeError("Not connected")
        tools_result = await self.session.list_tools()
        return [t.name for t in tools_result.tools]

    async def call_tool(self, name, arguments):
        if not self.session:
            raise RuntimeError("Not connected")
        return await self.session.call_tool(name, arguments) 