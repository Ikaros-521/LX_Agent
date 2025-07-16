# 通用工具函数单元测试

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils import (
    is_windows, is_linux, is_macos,
    run_command, ensure_dir, is_path_allowed,
    get_file_type, format_size
)

class TestSystemFunctions(unittest.TestCase):
    """
    系统相关函数测试
    """
    
    @patch('platform.system')
    def test_is_windows(self, mock_system):
        """
        测试Windows系统检测函数
        """
        # 模拟Windows系统
        mock_system.return_value = "Windows"
        self.assertTrue(is_windows())
        
        # 模拟非Windows系统
        mock_system.return_value = "Linux"
        self.assertFalse(is_windows())
    
    @patch('platform.system')
    def test_is_linux(self, mock_system):
        """
        测试Linux系统检测函数
        """
        # 模拟Linux系统
        mock_system.return_value = "Linux"
        self.assertTrue(is_linux())
        
        # 模拟非Linux系统
        mock_system.return_value = "Windows"
        self.assertFalse(is_linux())
    
    @patch('platform.system')
    def test_is_macos(self, mock_system):
        """
        测试macOS系统检测函数
        """
        # 模拟macOS系统
        mock_system.return_value = "Darwin"
        self.assertTrue(is_macos())
        
        # 模拟非macOS系统
        mock_system.return_value = "Windows"
        self.assertFalse(is_macos())

class TestCommandFunctions(unittest.TestCase):
    """
    命令相关函数测试
    """
    
    @patch('subprocess.run')
    def test_run_command(self, mock_run):
        """
        测试运行命令函数
        """
        # 模拟命令执行结果
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "命令执行成功"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # 测试执行命令
        result = run_command("test command")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "命令执行成功")
        self.assertEqual(result["stderr"], "")
        mock_run.assert_called_with("test command", shell=True, capture_output=True, text=True)
        
        # 测试命令执行失败
        mock_result.returncode = 1
        mock_result.stderr = "命令执行失败"
        result = run_command("test command")
        self.assertEqual(result["returncode"], 1)
        self.assertEqual(result["stdout"], "命令执行成功")
        self.assertEqual(result["stderr"], "命令执行失败")
        
        # 测试命令执行异常
        mock_run.side_effect = Exception("执行异常")
        result = run_command("test command")
        self.assertEqual(result["returncode"], -1)
        self.assertEqual(result["stdout"], "")
        self.assertEqual(result["stderr"], "执行异常")

class TestFileFunctions(unittest.TestCase):
    """
    文件相关函数测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()
        
        # 创建测试文件
        self.test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("测试内容")
    
    def tearDown(self):
        """
        测试后清理
        """
        # 删除临时测试目录
        shutil.rmtree(self.test_dir)
    
    def test_ensure_dir(self):
        """
        测试确保目录存在函数
        """
        # 测试创建新目录
        new_dir = os.path.join(self.test_dir, "new_dir")
        ensure_dir(new_dir)
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))
        
        # 测试已存在的目录
        ensure_dir(self.test_dir)
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.isdir(self.test_dir))
        
        # 测试嵌套目录
        nested_dir = os.path.join(self.test_dir, "nested", "dir")
        ensure_dir(nested_dir)
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.isdir(nested_dir))
    
    def test_is_path_allowed(self):
        """
        测试路径权限检查函数
        """
        # 测试允许的路径
        allowed_paths = [self.test_dir, "D:/Company"]
        self.assertTrue(is_path_allowed(self.test_dir, allowed_paths))
        self.assertTrue(is_path_allowed(self.test_file, allowed_paths))
        self.assertTrue(is_path_allowed("D:/Company/project", allowed_paths))
        
        # 测试不允许的路径
        self.assertFalse(is_path_allowed("/tmp", allowed_paths))
        self.assertFalse(is_path_allowed("C:/Windows", allowed_paths))
        
        # 测试空路径列表
        self.assertFalse(is_path_allowed(self.test_dir, []))
        
        # 测试None路径列表
        self.assertFalse(is_path_allowed(self.test_dir, None))
    
    def test_get_file_type(self):
        """
        测试获取文件类型函数
        """
        # 测试文本文件
        self.assertEqual(get_file_type(self.test_file), "text")
        
        # 测试目录
        self.assertEqual(get_file_type(self.test_dir), "directory")
        
        # 测试不存在的文件
        with self.assertRaises(FileNotFoundError):
            get_file_type(os.path.join(self.test_dir, "not_exist.txt"))
        
        # 创建二进制文件
        binary_file = os.path.join(self.test_dir, "binary_file.bin")
        with open(binary_file, "wb") as f:
            f.write(bytes([0x00, 0x01, 0x02, 0x03]))
        
        # 测试二进制文件
        self.assertEqual(get_file_type(binary_file), "binary")
    
    def test_format_size(self):
        """
        测试格式化文件大小函数
        """
        # 测试字节
        self.assertEqual(format_size(100), "100.0 B")
        
        # 测试KB
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1500), "1.5 KB")
        
        # 测试MB
        self.assertEqual(format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(format_size(1.5 * 1024 * 1024), "1.5 MB")
        
        # 测试GB
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.0 GB")
        self.assertEqual(format_size(2.5 * 1024 * 1024 * 1024), "2.5 GB")
        
        # 测试TB
        self.assertEqual(format_size(1024 * 1024 * 1024 * 1024), "1.0 TB")
        
        # 测试0
        self.assertEqual(format_size(0), "0.0 B")
        
        # 测试负数
        with self.assertRaises(ValueError):
            format_size(-1)

if __name__ == "__main__":
    unittest.main()