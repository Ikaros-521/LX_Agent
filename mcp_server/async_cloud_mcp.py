from mcp.client.streamable_http import streamablehttp_client
import asyncio
from loguru import logger

class AsyncCloudMCPAdapter:
    def __init__(self, config):
        if isinstance(config, dict):
            self.config = config
            self.url = config.get("url")
            self.api_key = config.get("api_key")
            self.timeout = config.get("timeout", 360)  # 增加默认超时时间到60秒
            self.capabilities = []  # 初始化为空，完全依赖云端
        else:
            self.config = None
            self.url = config
            self.api_key = None
            self.timeout = 360  # 增加默认超时时间到60秒
            self.capabilities = []
        self.session = None
        self.client = None
        self.max_retries = 2  # 添加重试次数

    async def connect(self):
        import mcp  # 避免循环依赖
        import traceback
        
        logger.info(f"正在连接到MCP服务: {self.url}")
        
        # 添加重试逻辑
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            if retry_count > 0:
                logger.info(f"第 {retry_count} 次重试连接MCP服务...")
                
            try:
                # 修正：使用 async with 而不是 await
                async with streamablehttp_client(self.url, timeout=self.timeout) as client:
                    read_stream, write_stream, response_info = client
                    
                    # 添加响应信息日志
                    if hasattr(response_info, 'status'):
                        logger.info(f"HTTP响应状态码: {response_info.status}")
                    
                    # 创建会话但不使用上下文管理器，因为我们需要保持会话开放
                    self.session = mcp.ClientSession(read_stream, write_stream)
                    
                    # 添加超时控制，避免initialize阻塞
                    logger.debug("初始化MCP会话...")
                    # 增加初始化超时时间
                    await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
                    
                    # 自动获取能力
                    try:
                        logger.debug("获取工具列表...")
                        tools_result = await asyncio.wait_for(self.session.list_tools(), timeout=self.timeout)
                        self.capabilities = [t.name for t in tools_result.tools]
                        logger.info(f"成功获取工具列表: {self.capabilities}")
                    except (asyncio.TimeoutError, Exception) as e:
                        self.capabilities = []
                        logger.warning(f"获取工具列表失败: {str(e)}")
                        logger.debug(f"详细错误: {traceback.format_exc()}")
                    
                    # 保存客户端连接以便后续使用
                    self.client = client
                    
                    # 连接成功，跳出重试循环
                    return
                
            except asyncio.TimeoutError:
                # 处理超时情况
                last_error = f"连接到MCP服务器超时 (>{self.timeout}秒)"
                logger.error(last_error)
                await self.disconnect()  # 确保资源被释放
                
                # 如果已达到最大重试次数，则抛出异常
                if retry_count >= self.max_retries:
                    raise RuntimeError(last_error)
                
                # 否则继续重试
                retry_count += 1
                
            except Exception as e:
                # 处理其他异常
                last_error = f"连接到MCP服务器失败: {str(e)}"
                logger.error(last_error)
                logger.debug(f"详细错误堆栈: {traceback.format_exc()}")
                await self.disconnect()  # 确保资源被释放
                
                # 如果已达到最大重试次数，则抛出异常
                if retry_count >= self.max_retries:
                    raise RuntimeError(last_error)
                
                # 否则继续重试
                retry_count += 1

    
    async def disconnect(self):
        # 移除对不存在的 close 方法的调用
        # ClientSession 对象可能没有 close 方法
        # 只需要将引用设置为 None 即可
        self.session = None
        
        # 如果 client 有 close 或 aclose 方法，则调用它
        if self.client:
            if hasattr(self.client, 'close'):
                await self.client.close()
            elif hasattr(self.client, 'aclose'):
                await self.client.aclose()
    
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