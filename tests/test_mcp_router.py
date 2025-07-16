# MCP路由器和工厂类单元测试

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.base import BaseMCP
from mcp.factory import MCPFactory
from mcp.router import MCPRouter
from mcp.local_mcp import LocalMCPAdapter
from mcp.cloud_mcp import CloudMCPAdapter

class MockMCP(BaseMCP):
    """
    用于测试的模拟MCP适配器
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.connected = False
        self.commands = []
        self.should_fail = False
        self.capabilities = config.get("capabilities", [])
        self.name = config.get("name", "mock")
    
    def connect(self):
        if self.should_fail:
            return False
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False
        return True
    
    def execute_command(self, command):
        if not self.connected:
            return {"status": "error", "error": "Not connected"}
        
        if self.should_fail:
            return {"status": "error", "error": "Command execution failed"}
        
        self.commands.append(command)
        return {"status": "success", "result": f"Executed: {command}"}
    
    def get_status(self):
        return {"connected": self.connected, "commands": len(self.commands)}
    
    def get_capabilities(self):
        return self.capabilities
    
    def is_available(self):
        return not self.should_fail

class TestMCPFactory(unittest.TestCase):
    """
    MCPFactory类测试
    """
    
    def test_create_local_mcp(self):
        """
        测试创建本地MCP适配器
        """
        config = {
            "type": "local",
            "enabled": True,
            "priority": 10,
            "capabilities": ["file", "process"]
        }
        
        mcp = MCPFactory.create(config)
        
        self.assertIsInstance(mcp, LocalMCPAdapter)
        self.assertEqual(mcp.config, config)
        self.assertEqual(mcp.get_capabilities(), ["file", "process"])
    
    def test_create_cloud_mcp(self):
        """
        测试创建云端MCP适配器
        """
        config = {
            "type": "cloud",
            "enabled": True,
            "priority": 5,
            "capabilities": ["browser", "mouse", "keyboard"],
            "url": "https://example.com/api",
            "api_key": "test_key"
        }
        
        mcp = MCPFactory.create(config)
        
        self.assertIsInstance(mcp, CloudMCPAdapter)
        self.assertEqual(mcp.config, config)
        self.assertEqual(mcp.get_capabilities(), ["browser", "mouse", "keyboard"])
    
    @patch('importlib.import_module')
    def test_create_custom_mcp(self, mock_import):
        """
        测试创建自定义MCP适配器
        """
        # 模拟导入模块
        mock_module = MagicMock()
        mock_module.CustomMCP = MockMCP
        mock_import.return_value = mock_module
        
        config = {
            "type": "custom",
            "enabled": True,
            "priority": 8,
            "capabilities": ["custom1", "custom2"],
            "module": "custom_module",
            "class": "CustomMCP"
        }
        
        mcp = MCPFactory.create(config)
        
        self.assertIsInstance(mcp, MockMCP)
        self.assertEqual(mcp.config, config)
        self.assertEqual(mcp.get_capabilities(), ["custom1", "custom2"])
        mock_import.assert_called_with("custom_module")
    
    def test_create_unknown_type(self):
        """
        测试创建未知类型的MCP适配器
        """
        config = {
            "type": "unknown",
            "enabled": True,
            "priority": 1,
            "capabilities": []
        }
        
        with self.assertRaises(ValueError):
            MCPFactory.create(config)

class TestMCPRouter(unittest.TestCase):
    """
    MCPRouter类测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        # 测试配置
        self.config = {
            "routing_strategy": "capability_match",
            "services": {
                "local": {
                    "type": "mock",
                    "name": "local",
                    "enabled": True,
                    "priority": 10,
                    "capabilities": ["file", "process"]
                },
                "cloud": {
                    "type": "mock",
                    "name": "cloud",
                    "enabled": True,
                    "priority": 5,
                    "capabilities": ["browser", "mouse", "keyboard"]
                },
                "disabled": {
                    "type": "mock",
                    "name": "disabled",
                    "enabled": False,
                    "priority": 1,
                    "capabilities": ["disabled"]
                }
            }
        }
        
        # 创建模拟MCP适配器
        self.local_mcp = MockMCP(self.config["services"]["local"])
        self.cloud_mcp = MockMCP(self.config["services"]["cloud"])
        
        # 创建MCP路由器
        self.router = MCPRouter(self.config)
        
        # 替换MCPFactory.create方法
        self.original_create = MCPFactory.create
        MCPFactory.create = lambda config: MockMCP(config)
    
    def tearDown(self):
        """
        测试后清理
        """
        # 恢复MCPFactory.create方法
        MCPFactory.create = self.original_create
    
    def test_initialize(self):
        """
        测试初始化方法
        """
        # 初始化路由器
        result = self.router.initialize()
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(len(self.router.mcps), 2)  # 只有两个启用的MCP
        
        # 验证MCP是否已连接
        for mcp in self.router.mcps.values():
            self.assertTrue(mcp.connected)
    
    def test_initialize_failure(self):
        """
        测试初始化失败
        """
        # 创建新的路由器
        router = MCPRouter(self.config)
        
        # 设置MCP连接失败
        for mcp_name in self.config["services"]:
            if self.config["services"][mcp_name]["enabled"]:
                config = self.config["services"][mcp_name].copy()
                config["should_fail"] = True
                router.mcps[mcp_name] = MockMCP(config)
        
        # 初始化路由器
        result = router.initialize()
        
        # 验证结果
        self.assertFalse(result)
    
    def test_get_available_mcps(self):
        """
        测试获取可用MCP方法
        """
        # 初始化路由器
        self.router.initialize()
        
        # 获取可用MCP
        mcps = self.router.get_available_mcps()
        
        # 验证结果
        self.assertEqual(len(mcps), 2)  # 两个可用的MCP
        self.assertIn("local", mcps)
        self.assertIn("cloud", mcps)
        
        # 设置一个MCP不可用
        self.router.mcps["local"].should_fail = True
        
        # 再次获取可用MCP
        mcps = self.router.get_available_mcps()
        
        # 验证结果
        self.assertEqual(len(mcps), 1)  # 只有一个可用的MCP
        self.assertIn("cloud", mcps)
    
    def test_select_mcp_by_capability(self):
        """
        测试按能力选择MCP方法
        """
        # 初始化路由器
        self.router.initialize()
        
        # 按文件能力选择MCP
        mcp = self.router.select_mcp_by_capability(["file"])
        self.assertEqual(mcp.name, "local")
        
        # 按浏览器能力选择MCP
        mcp = self.router.select_mcp_by_capability(["browser"])
        self.assertEqual(mcp.name, "cloud")
        
        # 按多个能力选择MCP
        mcp = self.router.select_mcp_by_capability(["file", "process"])
        self.assertEqual(mcp.name, "local")
        
        # 按不存在的能力选择MCP
        mcp = self.router.select_mcp_by_capability(["not_exist"])
        self.assertIsNone(mcp)
        
        # 设置一个MCP不可用
        self.router.mcps["local"].should_fail = True
        
        # 再次按文件能力选择MCP
        mcp = self.router.select_mcp_by_capability(["file"])
        self.assertIsNone(mcp)  # 没有可用的MCP具有文件能力
    
    def test_select_mcp_by_priority(self):
        """
        测试按优先级选择MCP方法
        """
        # 初始化路由器
        self.router.initialize()
        
        # 按优先级选择MCP
        mcp = self.router.select_mcp_by_priority()
        self.assertEqual(mcp.name, "local")  # 本地MCP优先级更高
        
        # 设置本地MCP不可用
        self.router.mcps["local"].should_fail = True
        
        # 再次按优先级选择MCP
        mcp = self.router.select_mcp_by_priority()
        self.assertEqual(mcp.name, "cloud")  # 云端MCP是下一个可用的
        
        # 设置所有MCP不可用
        self.router.mcps["cloud"].should_fail = True
        
        # 再次按优先级选择MCP
        mcp = self.router.select_mcp_by_priority()
        self.assertIsNone(mcp)  # 没有可用的MCP
    
    def test_select_mcp_by_load_balance(self):
        """
        测试按负载均衡选择MCP方法
        """
        # 初始化路由器
        self.router.initialize()
        
        # 设置路由策略为负载均衡
        self.router.routing_strategy = "load_balance"
        
        # 按负载均衡选择MCP
        mcp1 = self.router.select_mcp()
        self.assertIsNotNone(mcp1)
        
        # 执行一些命令
        mcp1.execute_command("command1")
        mcp1.execute_command("command2")
        
        # 再次按负载均衡选择MCP
        mcp2 = self.router.select_mcp()
        self.assertIsNotNone(mcp2)
        self.assertNotEqual(mcp1.name, mcp2.name)  # 应该选择不同的MCP
    
    def test_execute_command(self):
        """
        测试执行命令方法
        """
        # 初始化路由器
        self.router.initialize()
        
        # 执行命令
        result = self.router.execute_command("test command")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "Executed: test command")
        
        # 验证命令是否被执行
        self.assertIn("test command", self.router.mcps["local"].commands)
    
    def test_execute_command_with_capability(self):
        """
        测试按能力执行命令方法
        """
        # 初始化路由器
        self.router.initialize()
        
        # 按浏览器能力执行命令
        result = self.router.execute_command("open browser", ["browser"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "Executed: open browser")
        
        # 验证命令是否被正确的MCP执行
        self.assertIn("open browser", self.router.mcps["cloud"].commands)
        self.assertNotIn("open browser", self.router.mcps["local"].commands)
    
    def test_execute_command_failover(self):
        """
        测试命令执行故障转移
        """
        # 初始化路由器
        self.router.initialize()
        
        # 设置本地MCP执行命令失败
        self.router.mcps["local"].should_fail = True
        
        # 执行命令
        result = self.router.execute_command("test command")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "Executed: test command")
        
        # 验证命令是否被云端MCP执行
        self.assertIn("test command", self.router.mcps["cloud"].commands)
    
    def test_execute_command_all_fail(self):
        """
        测试所有MCP执行命令失败
        """
        # 初始化路由器
        self.router.initialize()
        
        # 设置所有MCP执行命令失败
        for mcp in self.router.mcps.values():
            mcp.should_fail = True
        
        # 执行命令
        result = self.router.execute_command("test command")
        self.assertEqual(result["status"], "error")
        self.assertIn("All MCPs failed", result["error"])
    
    def test_close(self):
        """
        测试关闭方法
        """
        # 初始化路由器
        self.router.initialize()
        
        # 关闭路由器
        self.router.close()
        
        # 验证所有MCP是否已断开连接
        for mcp in self.router.mcps.values():
            self.assertFalse(mcp.connected)

if __name__ == "__main__":
    unittest.main()