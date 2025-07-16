# 测试LLM模块

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm.base import BaseLLM
from llm.openai import OpenAILLM
from llm.anthropic import AnthropicLLM
from llm.local import LocalLLM
from llm.factory import LLMFactory
from config import Config


class TestLLMFactory(unittest.TestCase):
    """测试LLM工厂类"""
    
    def setUp(self):
        # 创建测试配置
        self.test_config = {
            "llm": {
                "default": "openai",
                "openai": {
                    "api_key": "test_openai_key",
                    "model": "gpt-4"
                },
                "anthropic": {
                    "api_key": "test_anthropic_key",
                    "model": "claude-3-opus-20240229"
                },
                "local": {
                    "model_path": "./models/llama2",
                    "device": "cpu"
                }
            }
        }
        self.config = Config(config_dict=self.test_config)
    
    def test_create_openai_llm(self):
        """测试创建OpenAI LLM"""
        factory = LLMFactory()
        llm = factory.create("openai", self.test_config["llm"]["openai"])
        self.assertIsInstance(llm, OpenAILLM)
        self.assertEqual(llm.api_key, "test_openai_key")
        self.assertEqual(llm.model, "gpt-4")
    
    def test_create_anthropic_llm(self):
        """测试创建Anthropic LLM"""
        factory = LLMFactory()
        llm = factory.create("anthropic", self.test_config["llm"]["anthropic"])
        self.assertIsInstance(llm, AnthropicLLM)
        self.assertEqual(llm.api_key, "test_anthropic_key")
        self.assertEqual(llm.model, "claude-3-opus-20240229")
    
    def test_create_local_llm(self):
        """测试创建Local LLM"""
        factory = LLMFactory()
        llm = factory.create("local", self.test_config["llm"]["local"])
        self.assertIsInstance(llm, LocalLLM)
        self.assertEqual(llm.model_path, "./models/llama2")
        self.assertEqual(llm.device, "cpu")
    
    def test_create_from_config(self):
        """测试从配置创建默认LLM"""
        factory = LLMFactory()
        llm = factory.create_from_config(self.config)
        self.assertIsInstance(llm, OpenAILLM)
        self.assertEqual(llm.api_key, "test_openai_key")
        self.assertEqual(llm.model, "gpt-4")


class TestOpenAILLM(unittest.TestCase):
    """测试OpenAI LLM实现"""
    
    def setUp(self):
        self.config = {
            "api_key": "test_openai_key",
            "model": "gpt-4"
        }
        self.llm = OpenAILLM(self.config)
    
    @patch('llm.openai.openai.ChatCompletion.create')
    def test_generate(self, mock_create):
        """测试文本生成"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {"content": "测试回复"}
        mock_create.return_value = mock_response
        
        # 调用generate方法
        result = self.llm.generate("测试提示")
        
        # 验证结果
        self.assertEqual(result, "测试回复")
        mock_create.assert_called_once()
    
    @patch('llm.openai.openai.Embedding.create')
    def test_get_embeddings(self, mock_create):
        """测试获取嵌入向量"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        mock_create.return_value = mock_response
        
        # 调用get_embeddings方法
        result = self.llm.get_embeddings("测试文本")
        
        # 验证结果
        self.assertEqual(result, [0.1, 0.2, 0.3])
        mock_create.assert_called_once()
    
    @patch('llm.openai.openai.ChatCompletion.create')
    def test_analyze_command(self, mock_create):
        """测试命令分析"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {"content": json.dumps({"capabilities": ["browser", "mouse"]})}
        mock_create.return_value = mock_response
        
        # 调用analyze_command方法
        result = self.llm.analyze_command("打开浏览器并点击登录按钮")
        
        # 验证结果
        self.assertEqual(result, ["browser", "mouse"])
        mock_create.assert_called_once()
    
    @patch('llm.openai.openai.ChatCompletion.create')
    def test_summarize_result(self, mock_create):
        """测试结果总结"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {"content": "成功打开浏览器并点击了登录按钮"}
        mock_create.return_value = mock_response
        
        # 调用summarize_result方法
        command = "打开浏览器并点击登录按钮"
        result = {
            "status": "success",
            "stdout": "浏览器已打开，已点击登录按钮"
        }
        summary = self.llm.summarize_result(command, result)
        
        # 验证结果
        self.assertEqual(summary, "成功打开浏览器并点击了登录按钮")
        mock_create.assert_called_once()


if __name__ == "__main__":
    unittest.main()