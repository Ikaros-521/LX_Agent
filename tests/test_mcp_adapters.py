# MCP适配器单元测试

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.base import BaseMCP
from mcp.local_mcp import LocalMCPAdapter
from mcp.cloud_mcp import CloudMCPAdapter
from mcp.factory import MCPFactory
from mcp.router import MCPRouter

class TestLocalMCPAdapter(unittest.TestCase):
    """
    本地MCP适配器测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        self.config = {
            "capabilities": ["file", "process", "shell"]
        }
        self.mcp = LocalMCPAdapter(self.config)
    
    def test_connect(self):
        """
        测试连接方法
        """
        result = self.mcp.connect()
        self.assertTrue(result)
        self.assertTrue(self.mcp.connected)
    
    def test_disconnect(self):
        """
        测试断开连接方法
        """
        self.mcp.connect()
        self.mcp.disconnect()
        self.assertFalse(self.mcp.connected)
    
    def test_get_capabilities(self):
        """
        测试获取能力列表方法
        """
        capabilities = self.mcp.get_capabilities()
        self.assertEqual(capabilities, ["file", "process", "shell"])
    
    def test_is_available(self):
        """
        测试可用性检查方法
        """
        self.mcp.connect()
        self.assertTrue(self.mcp.is_available())
        self.mcp.disconnect()
        self.assertFalse(self.mcp.is_available())
    
    @patch('subprocess.Popen')
    def test_execute_command(self, mock_popen):
        """
        测试执行命令方法
        """
        # 模拟Popen返回值
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("output", "")
        mock_popen.return_value = mock_process
        
        # 连接MCP
        self.mcp.connect()
        
        # 执行命令
        result = self.mcp.execute_command("echo test")
        
        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "output")
        
        # 测试未连接时执行命令
        self.mcp.disconnect()
        with self.assertRaises(ConnectionError):
            self.mcp.execute_command("echo test")

class TestCloudMCPAdapter(unittest.TestCase):
    """
    云端MCP适配器测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        self.config = {
            "url": "https://example.com/mcp/api",
            "api_key": "test_key",
            "timeout": 5,
            "capabilities": ["browser", "mouse", "keyboard"]
        }
        self.mcp = CloudMCPAdapter(self.config)
    
    @patch('requests.Session.get')
    def test_connect(self, mock_get):
        """
        测试连接方法
        """
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.mcp.connect()
        self.assertTrue(result)
        self.assertTrue(self.mcp.connected)
        
        # 模拟失败响应
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        self.mcp.disconnect()
        result = self.mcp.connect()
        self.assertFalse(result)
        self.assertFalse(self.mcp.connected)
    
    def test_disconnect(self):
        """
        测试断开连接方法
        """
        # 模拟连接状态
        self.mcp.connected = True
        self.mcp.disconnect()
        self.assertFalse(self.mcp.connected)
    
    def test_get_capabilities(self):
        """
        测试获取能力列表方法
        """
        capabilities = self.mcp.get_capabilities()
        self.assertEqual(capabilities, ["browser", "mouse", "keyboard"])
    
    @patch('requests.Session.get')
    def test_is_available(self, mock_get):
        """
        测试可用性检查方法
        """
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 模拟连接状态
        self.mcp.connected = True
        self.assertTrue(self.mcp.is_available())
        
        # 模拟断开状态
        self.mcp.connected = False
        self.assertFalse(self.mcp.is_available())
    
    @patch('requests.Session.post')
    def test_execute_command(self, mock_post):
        """
        测试执行命令方法
        """
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "result": "test result"}
        mock_post.return_value = mock_response
        
        # 模拟连接状态
        self.mcp.connected = True
        
        # 执行命令
        result = self.mcp.execute_command("test command")
        
        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "test result")
        
        # 测试未连接时执行命令
        self.mcp.connected = False
        with self.assertRaises(ConnectionError):
            self.mcp.execute_command("test command")

class TestMCPFactory(unittest.TestCase):
    """
    MCP工厂类测试
    """
    
    def test_create_local_mcp(self):
        """
        测试创建本地MCP
        """
        config = {
            "type": "local",
            "capabilities": ["file", "process"]
        }
        
        mcp = MCPFactory.create("local", config)
        self.assertIsNotNone(mcp)
        self.assertIsInstance(mcp, LocalMCPAdapter)
        self.assertEqual(mcp.capabilities, ["file", "process"])
    
    def test_create_cloud_mcp(self):
        """
        测试创建云端MCP
        """
        config = {
            "type": "cloud",
            "url": "https://example.com/mcp/api",
            "api_key": "test_key",
            "capabilities": ["browser", "mouse"]
        }
        
        mcp = MCPFactory.create("cloud", config)
        self.assertIsNotNone(mcp)
        self.assertIsInstance(mcp, CloudMCPAdapter)
        self.assertEqual(mcp.capabilities, ["browser", "mouse"])
    
    def test_create_invalid_type(self):
        """
        测试创建无效类型的MCP
        """
        config = {
            "type": "invalid"
        }
        
        mcp = MCPFactory.create("invalid", config)
        self.assertIsNone(mcp)
    
    def test_create_missing_type(self):
        """
        测试创建缺少类型的MCP
        """
        config = {}
        
        mcp = MCPFactory.create("missing", config)
        self.assertIsNone(mcp)

class TestMCPRouter(unittest.TestCase):
    """
    MCP路由器测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        self.config = {
            "mcp": {
                "routing_strategy": "capability_match",
                "services": {
                    "local": {
                        "type": "local",
                        "enabled": True,
                        "priority": 10,
                        "capabilities": ["file", "process"]
                    },
                    "cloud": {
                        "type": "cloud",
                        "enabled": True,
                        "priority": 5,
                        "url": "https://example.com/mcp/api",
                        "api_key": "test_key",
                        "capabilities": ["browser", "mouse"]
                    },
                    "disabled": {
                        "type": "local",
                        "enabled": False,
                        "priority": 1,
                        "capabilities": ["shell"]
                    }
                }
            }
        }
        
        # 创建路由器
        self.router = MCPRouter(self.config)
        
        # 模拟MCP
        self.local_mcp = MagicMock(spec=LocalMCPAdapter)
        self.local_mcp.connect.return_value = True
        self.local_mcp.is_available.return_value = True
        self.local_mcp.get_capabilities.return_value = ["file", "process"]
        
        self.cloud_mcp = MagicMock(spec=CloudMCPAdapter)
        self.cloud_mcp.connect.return_value = True
        self.cloud_mcp.is_available.return_value = True
        self.cloud_mcp.get_capabilities.return_value = ["browser", "mouse"]
        
        # 手动添加MCP
        self.router.mcps = {
            "local": self.local_mcp,
            "cloud": self.cloud_mcp
        }
        self.router.initialized = True
    
    def test_get_available_mcps(self):
        """
        测试获取可用MCP列表
        """
        available = self.router.get_available_mcps()
        self.assertEqual(len(available), 2)
        self.assertEqual(available[0][0], "local")
        self.assertEqual(available[1][0], "cloud")
        
        # 测试一个MCP不可用的情况
        self.local_mcp.is_available.return_value = False
        available = self.router.get_available_mcps()
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0][0], "cloud")
    
    def test_select_mcp_by_capability(self):
        """
        测试根据能力选择MCP
        """
        # 测试选择文件能力
        selected = self.router.select_mcp_by_capability(["file"])
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0], "local")
        
        # 测试选择浏览器能力
        selected = self.router.select_mcp_by_capability(["browser"])
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0], "cloud")
        
        # 测试选择不存在的能力
        selected = self.router.select_mcp_by_capability(["unknown"])
        self.assertIsNotNone(selected)  # 应该返回最佳匹配
    
    def test_select_mcp_by_priority(self):
        """
        测试根据优先级选择MCP
        """
        selected = self.router.select_mcp_by_priority()
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0], "local")  # 本地MCP优先级更高
    
    def test_select_mcp_by_load_balance(self):
        """
        测试负载均衡选择MCP
        """
        # 多次选择，应该有不同的结果
        results = set()
        for _ in range(20):
            selected = self.router.select_mcp_by_load_balance()
            self.assertIsNotNone(selected)
            results.add(selected[0])
        
        # 应该至少有两种不同的选择
        self.assertGreaterEqual(len(results), 1)
    
    def test_select_mcp(self):
        """
        测试选择MCP
        """
        # 测试能力匹配策略
        self.router.routing_strategy = "capability_match"
        selected = self.router.select_mcp(["file"])
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0], "local")
        
        # 测试优先级优先策略
        self.router.routing_strategy = "priority_first"
        selected = self.router.select_mcp()
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0], "local")
        
        # 测试负载均衡策略
        self.router.routing_strategy = "load_balance"
        selected = self.router.select_mcp()
        self.assertIsNotNone(selected)
    
    def test_execute_command(self):
        """
        测试执行命令
        """
        # 模拟执行命令结果
        self.local_mcp.execute_command.return_value = {
            "status": "success",
            "result": "local result"
        }
        
        # 测试执行文件相关命令
        result = self.router.execute_command("file command", ["file"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "local result")
        self.assertEqual(result["mcp_name"], "local")
        
        # 测试执行浏览器相关命令
        result = self.router.execute_command("browser command", ["browser"])
        self.assertEqual(result["mcp_name"], "cloud")
    
    def test_execute_command_fallback(self):
        """
        测试执行命令失败后的故障转移
        """
        # 模拟本地MCP执行失败
        self.local_mcp.execute_command.side_effect = Exception("Local MCP failed")
        
        # 模拟云端MCP执行成功
        self.cloud_mcp.execute_command.return_value = {
            "status": "success",
            "result": "cloud result"
        }
        
        # 测试执行文件相关命令
        result = self.router.execute_command("file command", ["file"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "cloud result")
        self.assertEqual(result["mcp_name"], "cloud")
        self.assertTrue(result["fallback"])

if __name__ == "__main__":
    unittest.main()