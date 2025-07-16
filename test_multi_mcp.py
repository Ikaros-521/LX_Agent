# 多MCP功能测试脚本

import os
import sys
import logging

from config import Config
from logger import setup_logging
from mcp.router import MCPRouter
from mcp.local_mcp import LocalMCPAdapter
from mcp.cloud_mcp import CloudMCPAdapter

# 设置日志
setup_logging({"level": "DEBUG"})
logger = logging.getLogger(__name__)

def test_mcp_router():
    """
    测试MCP路由器功能
    """
    # 创建测试配置
    test_config = {
        "mcp": {
            "routing_strategy": "capability_match",
            "services": {
                "local": {
                    "type": "local",
                    "enabled": True,
                    "priority": 10,
                    "capabilities": ["file", "process", "shell"]
                },
                "mock_cloud": {
                    "type": "custom",
                    "enabled": True,
                    "priority": 5,
                    "capabilities": ["browser", "mouse", "keyboard"]
                }
            }
        }
    }
    
    # 创建模拟的云端MCP
    class MockCloudMCP(CloudMCPAdapter):
        def __init__(self, config):
            self.config = config
            self.capabilities = config.get("capabilities", [])
            self.connected = False
            
        def connect(self):
            self.connected = True
            return True
            
        def disconnect(self):
            self.connected = False
            
        def execute_command(self, command, **kwargs):
            return {
                "status": "success",
                "result": f"Mock Cloud MCP executed: {command}"
            }
            
        def get_status(self):
            return {
                "status": "connected" if self.connected else "disconnected",
                "capabilities": self.capabilities
            }
            
        def get_capabilities(self):
            return self.capabilities
            
        def is_available(self):
            return self.connected
    
    # 创建MCP路由器
    router = MCPRouter(test_config)
    
    # 手动添加模拟的云端MCP
    mock_cloud = MockCloudMCP(test_config["mcp"]["services"]["mock_cloud"])
    mock_cloud.connect()
    router.mcps["mock_cloud"] = mock_cloud
    router.initialized = True
    
    # 测试1：根据能力选择MCP - 应该选择本地MCP
    logger.info("测试1：根据文件能力选择MCP")
    selected = router.select_mcp(["file"])
    if selected:
        name, mcp = selected
        logger.info(f"选择的MCP: {name}")
        assert name == "local", f"期望选择local MCP，实际选择了{name}"
    else:
        logger.error("未选择任何MCP")
        assert False, "未选择任何MCP"
    
    # 测试2：根据能力选择MCP - 应该选择模拟云端MCP
    logger.info("测试2：根据浏览器能力选择MCP")
    selected = router.select_mcp(["browser"])
    if selected:
        name, mcp = selected
        logger.info(f"选择的MCP: {name}")
        assert name == "mock_cloud", f"期望选择mock_cloud MCP，实际选择了{name}"
    else:
        logger.error("未选择任何MCP")
        assert False, "未选择任何MCP"
    
    # 测试3：根据优先级选择MCP
    logger.info("测试3：根据优先级选择MCP")
    router.routing_strategy = "priority_first"
    selected = router.select_mcp()
    if selected:
        name, mcp = selected
        logger.info(f"选择的MCP: {name}")
        assert name == "local", f"期望选择local MCP，实际选择了{name}"
    else:
        logger.error("未选择任何MCP")
        assert False, "未选择任何MCP"
    
    # 测试4：执行命令
    logger.info("测试4：执行命令")
    result = router.execute_command("echo hello", ["file"])
    logger.info(f"执行结果: {result}")
    assert result["status"] in ["success", "error"], "执行结果状态不正确"
    assert "mcp_name" in result, "执行结果中没有MCP名称"
    
    # 测试5：故障转移
    logger.info("测试5：故障转移测试")
    # 使本地MCP不可用
    local_mcp = router.mcps["local"]
    local_mcp.connected = False
    
    # 执行需要文件能力的命令，应该转移到mock_cloud
    result = router.execute_command("echo hello", ["file"])
    logger.info(f"执行结果: {result}")
    assert result["mcp_name"] == "mock_cloud", f"期望使用mock_cloud MCP，实际使用了{result.get('mcp_name')}"
    assert result.get("fallback") == True, "没有标记为故障转移"
    
    # 恢复本地MCP
    local_mcp.connected = True
    
    # 测试6：负载均衡
    logger.info("测试6：负载均衡测试")
    router.routing_strategy = "load_balance"
    
    # 执行多次命令，检查是否有负载均衡
    mcp_counts = {"local": 0, "mock_cloud": 0}
    for i in range(10):
        result = router.execute_command(f"command {i}")
        mcp_name = result.get("mcp_name")
        mcp_counts[mcp_name] = mcp_counts.get(mcp_name, 0) + 1
    
    logger.info(f"负载均衡结果: {mcp_counts}")
    assert mcp_counts["local"] > 0 and mcp_counts["mock_cloud"] > 0, "负载均衡失败，只使用了一个MCP"
    
    logger.info("所有测试通过！")

if __name__ == "__main__":
    test_mcp_router()