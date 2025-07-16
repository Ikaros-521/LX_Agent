# Config类单元测试

import os
import sys
import unittest
import tempfile
import yaml
from unittest.mock import patch, mock_open

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

class TestConfig(unittest.TestCase):
    """
    Config类测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        # 测试配置数据
        self.test_config = {
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "test_key"
            },
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
                        "capabilities": ["browser", "mouse", "keyboard"],
                        "url": "https://example.com/api",
                        "api_key": "cloud_key"
                    }
                }
            },
            "tools": {
                "file": {
                    "allowed_paths": ["D:/Company", "C:/Users"]
                },
                "process": {
                    "allowed_processes": ["notepad.exe", "chrome.exe"]
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/agent.log",
                "max_size": 10,
                "backup_count": 5
            }
        }
    
    def test_init_with_file(self):
        """
        测试从文件初始化配置
        """
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            yaml.dump(self.test_config, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # 从文件加载配置
            config = Config(temp_file_path)
            
            # 验证配置是否正确加载
            self.assertEqual(config.config, self.test_config)
            self.assertEqual(config.config_file, temp_file_path)
        finally:
            # 删除临时文件
            os.unlink(temp_file_path)
    
    def test_init_with_dict(self):
        """
        测试从字典初始化配置
        """
        # 从字典加载配置
        config = Config(config_dict=self.test_config)
        
        # 验证配置是否正确加载
        self.assertEqual(config.config, self.test_config)
        self.assertIsNone(config.config_file)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_config(self, mock_yaml_load, mock_file_open):
        """
        测试加载配置方法
        """
        # 设置模拟返回值
        mock_yaml_load.return_value = self.test_config
        
        # 加载配置
        config = Config()
        result = config.load_config("config.yaml")
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(config.config, self.test_config)
        self.assertEqual(config.config_file, "config.yaml")
        mock_file_open.assert_called_once_with("config.yaml", "r", encoding="utf-8")
        mock_yaml_load.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    def test_save_config(self, mock_yaml_dump, mock_file_open):
        """
        测试保存配置方法
        """
        # 创建配置对象
        config = Config(config_dict=self.test_config)
        config.config_file = "config.yaml"
        
        # 保存配置
        result = config.save_config()
        
        # 验证结果
        self.assertTrue(result)
        mock_file_open.assert_called_once_with("config.yaml", "w", encoding="utf-8")
        mock_yaml_dump.assert_called_once_with(self.test_config, mock_file_open())
    
    def test_get_set(self):
        """
        测试获取和设置配置项方法
        """
        # 创建配置对象
        config = Config(config_dict=self.test_config)
        
        # 测试获取配置项
        self.assertEqual(config.get("llm.provider"), "openai")
        self.assertEqual(config.get("mcp.services.local.priority"), 10)
        self.assertEqual(config.get("logging.level"), "INFO")
        
        # 测试获取不存在的配置项
        self.assertIsNone(config.get("not.exist"))
        self.assertEqual(config.get("not.exist", "default"), "default")
        
        # 测试设置配置项
        config.set("llm.provider", "azure")
        self.assertEqual(config.get("llm.provider"), "azure")
        
        config.set("mcp.services.local.priority", 20)
        self.assertEqual(config.get("mcp.services.local.priority"), 20)
        
        # 测试设置新配置项
        config.set("new.config", "value")
        self.assertEqual(config.get("new.config"), "value")
    
    def test_get_mcp_config(self):
        """
        测试获取MCP配置方法
        """
        # 创建配置对象
        config = Config(config_dict=self.test_config)
        
        # 获取MCP配置
        mcp_config = config.get_mcp_config()
        
        # 验证结果
        self.assertEqual(mcp_config, self.test_config["mcp"])
        self.assertEqual(mcp_config["routing_strategy"], "capability_match")
        self.assertEqual(len(mcp_config["services"]), 2)
        self.assertEqual(mcp_config["services"]["local"]["type"], "local")
        self.assertEqual(mcp_config["services"]["cloud"]["type"], "cloud")
    
    def test_get_llm_config(self):
        """
        测试获取LLM配置方法
        """
        # 创建配置对象
        config = Config(config_dict=self.test_config)
        
        # 获取LLM配置
        llm_config = config.get_llm_config()
        
        # 验证结果
        self.assertEqual(llm_config, self.test_config["llm"])
        self.assertEqual(llm_config["provider"], "openai")
        self.assertEqual(llm_config["model"], "gpt-4")
        self.assertEqual(llm_config["api_key"], "test_key")
    
    def test_get_tools_config(self):
        """
        测试获取工具配置方法
        """
        # 创建配置对象
        config = Config(config_dict=self.test_config)
        
        # 获取工具配置
        tools_config = config.get_tools_config()
        
        # 验证结果
        self.assertEqual(tools_config, self.test_config["tools"])
        self.assertEqual(tools_config["file"]["allowed_paths"], ["D:/Company", "C:/Users"])
        self.assertEqual(tools_config["process"]["allowed_processes"], ["notepad.exe", "chrome.exe"])
    
    def test_get_logging_config(self):
        """
        测试获取日志配置方法
        """
        # 创建配置对象
        config = Config(config_dict=self.test_config)
        
        # 获取日志配置
        logging_config = config.get_logging_config()
        
        # 验证结果
        self.assertEqual(logging_config, self.test_config["logging"])
        self.assertEqual(logging_config["level"], "INFO")
        self.assertEqual(logging_config["file"], "logs/agent.log")
        self.assertEqual(logging_config["max_size"], 10)
        self.assertEqual(logging_config["backup_count"], 5)

if __name__ == "__main__":
    unittest.main()