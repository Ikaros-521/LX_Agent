# 日志模块单元测试

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import logging
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging

class TestLogger(unittest.TestCase):
    """
    日志模块测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()
        
        # 测试日志配置
        self.log_config = {
            "level": "INFO",
            "file": os.path.join(self.test_dir, "logs", "test.log"),
            "max_size": 1,  # 1MB
            "backup_count": 3
        }
        
        # 保存原始日志配置
        self.root_logger = logging.getLogger()
        self.original_handlers = self.root_logger.handlers.copy()
        self.original_level = self.root_logger.level
    
    def tearDown(self):
        """
        测试后清理
        """
        # 恢复原始日志配置
        self.root_logger.handlers = self.original_handlers
        self.root_logger.setLevel(self.original_level)
        
        # 删除临时测试目录
        shutil.rmtree(self.test_dir)
    
    @patch('logging.getLogger')
    def test_setup_logging(self, mock_get_logger):
        """
        测试设置日志函数
        """
        # 模拟日志记录器
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # 设置日志
        logger = setup_logging(self.log_config)
        
        # 验证日志目录是否创建
        log_dir = os.path.dirname(self.log_config["file"])
        self.assertTrue(os.path.exists(log_dir))
        self.assertTrue(os.path.isdir(log_dir))
        
        # 验证日志级别是否设置正确
        mock_logger.setLevel.assert_called_with(logging.INFO)
        
        # 验证处理器是否添加
        self.assertEqual(mock_logger.addHandler.call_count, 2)  # 控制台和文件处理器
    
    def test_setup_logging_with_invalid_level(self):
        """
        测试设置无效日志级别
        """
        # 设置无效日志级别
        invalid_config = self.log_config.copy()
        invalid_config["level"] = "INVALID"
        
        # 设置日志
        logger = setup_logging(invalid_config)
        
        # 验证日志级别是否设置为默认值
        self.assertEqual(logger.level, logging.INFO)  # 默认为INFO级别
    
    def test_setup_logging_with_debug_level(self):
        """
        测试设置DEBUG日志级别
        """
        # 设置DEBUG日志级别
        debug_config = self.log_config.copy()
        debug_config["level"] = "DEBUG"
        
        # 设置日志
        logger = setup_logging(debug_config)
        
        # 验证日志级别是否设置为DEBUG
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_setup_logging_with_warning_level(self):
        """
        测试设置WARNING日志级别
        """
        # 设置WARNING日志级别
        warning_config = self.log_config.copy()
        warning_config["level"] = "WARNING"
        
        # 设置日志
        logger = setup_logging(warning_config)
        
        # 验证日志级别是否设置为WARNING
        self.assertEqual(logger.level, logging.WARNING)
    
    def test_setup_logging_with_error_level(self):
        """
        测试设置ERROR日志级别
        """
        # 设置ERROR日志级别
        error_config = self.log_config.copy()
        error_config["level"] = "ERROR"
        
        # 设置日志
        logger = setup_logging(error_config)
        
        # 验证日志级别是否设置为ERROR
        self.assertEqual(logger.level, logging.ERROR)
    
    def test_setup_logging_with_critical_level(self):
        """
        测试设置CRITICAL日志级别
        """
        # 设置CRITICAL日志级别
        critical_config = self.log_config.copy()
        critical_config["level"] = "CRITICAL"
        
        # 设置日志
        logger = setup_logging(critical_config)
        
        # 验证日志级别是否设置为CRITICAL
        self.assertEqual(logger.level, logging.CRITICAL)
    
    def test_setup_logging_without_file(self):
        """
        测试不设置日志文件
        """
        # 不设置日志文件
        no_file_config = self.log_config.copy()
        del no_file_config["file"]
        
        # 设置日志
        logger = setup_logging(no_file_config)
        
        # 验证只有控制台处理器
        handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
        self.assertEqual(len(handlers), 1)
    
    def test_setup_logging_with_logging(self):
        """
        测试实际记录日志
        """
        # 设置日志
        logger = setup_logging(self.log_config)
        
        # 记录日志
        logger.info("测试信息日志")
        logger.warning("测试警告日志")
        logger.error("测试错误日志")
        
        # 验证日志文件是否创建
        self.assertTrue(os.path.exists(self.log_config["file"]))
        
        # 验证日志内容
        with open(self.log_config["file"], "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn("测试信息日志", log_content)
            self.assertIn("测试警告日志", log_content)
            self.assertIn("测试错误日志", log_content)

if __name__ == "__main__":
    unittest.main()