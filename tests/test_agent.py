# Agent类单元测试

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from core.agent import Agent
from mcp.router import MCPRouter

class TestAgent(unittest.TestCase):
    """
    Agent类测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        # 模拟配置
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.config = {
            "mcp": {
                "routing_strategy": "capability_match",
                "services": {
                    "local": {
                        "type": "local",
                        "enabled": True,
                        "priority": 10,
                        "capabilities": ["file", "process"]
                    }
                }
            }
        }
        
        # 创建Agent
        self.agent = Agent(self.mock_config)
        
        # 模拟MCP路由器
        self.mock_router = MagicMock(spec=MCPRouter)
        self.mock_router.initialize.return_value = True
        self.mock_router.execute_command.return_value = {
            "status": "success",
            "result": "test result"
        }
        
        # 替换Agent的MCP路由器
        self.agent.mcp_router = self.mock_router
    
    def test_initialize(self):
        """
        测试初始化方法
        """
        result = self.agent.initialize()
        self.assertTrue(result)
        self.assertTrue(self.agent.initialized)
        self.mock_router.initialize.assert_called_once()
        
        # 测试初始化失败
        self.agent.initialized = False
        self.mock_router.initialize.return_value = False
        result = self.agent.initialize()
        self.assertFalse(result)
        self.assertFalse(self.agent.initialized)
    
    def test_execute(self):
        """
        测试执行命令方法
        """
        # 初始化Agent
        self.agent.initialized = True
        
        # 执行命令
        result = self.agent.execute("test command", ["file"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "test result")
        self.mock_router.execute_command.assert_called_with("test command", ["file"])
        
        # 测试未初始化时执行命令
        self.agent.initialized = False
        self.mock_router.initialize.return_value = False
        result = self.agent.execute("test command")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "Agent not initialized")
    
    def test_analyze_command(self):
        """
        测试分析命令方法
        """
        # 测试文件相关命令
        capabilities = self.agent.analyze_command("读取文件内容")
        self.assertIn("file", capabilities)
        
        # 测试浏览器相关命令
        capabilities = self.agent.analyze_command("打开浏览器访问网页")
        self.assertIn("browser", capabilities)
        
        # 测试进程相关命令
        capabilities = self.agent.analyze_command("运行程序并查看进程")
        self.assertIn("process", capabilities)
        
        # 测试鼠标相关命令
        capabilities = self.agent.analyze_command("移动鼠标并点击按钮")
        self.assertIn("mouse", capabilities)
        
        # 测试键盘相关命令
        capabilities = self.agent.analyze_command("输入文本并按回车键")
        self.assertIn("keyboard", capabilities)
    
    def test_execute_with_analysis(self):
        """
        测试分析并执行命令方法
        """
        # 初始化Agent
        self.agent.initialized = True
        
        # 模拟分析命令结果
        with patch.object(self.agent, 'analyze_command', return_value=["file"]):
            result = self.agent.execute_with_analysis("读取文件内容")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["result"], "test result")
            self.mock_router.execute_command.assert_called_with("读取文件内容", ["file"])
    
    def test_close(self):
        """
        测试关闭方法
        """
        # 初始化Agent
        self.agent.initialized = True
        
        # 关闭Agent
        self.agent.close()
        self.assertFalse(self.agent.initialized)
        self.mock_router.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()