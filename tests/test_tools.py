# 工具类单元测试

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.file_tool import FileTool
from tools.process_tool import ProcessTool

class TestFileTool(unittest.TestCase):
    """
    FileTool类测试
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
        
        # 创建FileTool实例
        self.file_tool = FileTool(allowed_paths=[self.test_dir])
    
    def tearDown(self):
        """
        测试后清理
        """
        # 删除临时测试目录
        shutil.rmtree(self.test_dir)
    
    def test_is_path_allowed(self):
        """
        测试路径权限检查方法
        """
        # 测试允许的路径
        self.assertTrue(self.file_tool.is_path_allowed(self.test_dir))
        self.assertTrue(self.file_tool.is_path_allowed(self.test_file))
        
        # 测试不允许的路径
        self.assertFalse(self.file_tool.is_path_allowed("/tmp"))
        self.assertFalse(self.file_tool.is_path_allowed("C:/Windows"))
    
    def test_list_dir(self):
        """
        测试列出目录方法
        """
        # 创建子目录
        sub_dir = os.path.join(self.test_dir, "sub_dir")
        os.makedirs(sub_dir)
        
        # 在子目录中创建文件
        sub_file = os.path.join(sub_dir, "sub_file.txt")
        with open(sub_file, "w", encoding="utf-8") as f:
            f.write("子目录测试内容")
        
        # 测试列出目录
        result = self.file_tool.list_dir(self.test_dir)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(len(result["dirs"]), 1)
        self.assertIn("test_file.txt", result["files"])
        self.assertIn("sub_dir", result["dirs"])
        
        # 测试列出子目录
        result = self.file_tool.list_dir(sub_dir)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(len(result["dirs"]), 0)
        self.assertIn("sub_file.txt", result["files"])
        
        # 测试列出不存在的目录
        result = self.file_tool.list_dir(os.path.join(self.test_dir, "not_exist"))
        self.assertEqual(result["status"], "error")
        self.assertIn("Directory not found", result["error"])
        
        # 测试列出不允许的目录
        result = self.file_tool.list_dir("/tmp")
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not allowed", result["error"])
    
    def test_read_file(self):
        """
        测试读取文件方法
        """
        # 测试读取文件
        result = self.file_tool.read_file(self.test_file)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["content"], "测试内容")
        
        # 测试读取不存在的文件
        result = self.file_tool.read_file(os.path.join(self.test_dir, "not_exist.txt"))
        self.assertEqual(result["status"], "error")
        self.assertIn("File not found", result["error"])
        
        # 测试读取不允许的文件
        result = self.file_tool.read_file("/etc/passwd")
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not allowed", result["error"])
    
    def test_write_file(self):
        """
        测试写入文件方法
        """
        # 测试写入新文件
        new_file = os.path.join(self.test_dir, "new_file.txt")
        result = self.file_tool.write_file(new_file, "新文件内容")
        self.assertEqual(result["status"], "success")
        
        # 验证文件内容
        with open(new_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "新文件内容")
        
        # 测试覆盖现有文件
        result = self.file_tool.write_file(self.test_file, "更新的内容")
        self.assertEqual(result["status"], "success")
        
        # 验证文件内容
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "更新的内容")
        
        # 测试写入不允许的文件
        result = self.file_tool.write_file("/etc/hosts", "测试内容")
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not allowed", result["error"])
    
    def test_delete(self):
        """
        测试删除文件或目录方法
        """
        # 测试删除文件
        result = self.file_tool.delete(self.test_file)
        self.assertEqual(result["status"], "success")
        self.assertFalse(os.path.exists(self.test_file))
        
        # 创建子目录
        sub_dir = os.path.join(self.test_dir, "sub_dir")
        os.makedirs(sub_dir)
        
        # 测试删除目录
        result = self.file_tool.delete(sub_dir)
        self.assertEqual(result["status"], "success")
        self.assertFalse(os.path.exists(sub_dir))
        
        # 测试删除不存在的文件
        result = self.file_tool.delete(os.path.join(self.test_dir, "not_exist.txt"))
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not found", result["error"])
        
        # 测试删除不允许的文件
        result = self.file_tool.delete("/etc/hosts")
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not allowed", result["error"])
    
    def test_copy(self):
        """
        测试复制文件或目录方法
        """
        # 测试复制文件
        dest_file = os.path.join(self.test_dir, "dest_file.txt")
        result = self.file_tool.copy(self.test_file, dest_file)
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(dest_file))
        
        # 验证文件内容
        with open(dest_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "测试内容")
        
        # 创建子目录和文件
        sub_dir = os.path.join(self.test_dir, "sub_dir")
        os.makedirs(sub_dir)
        sub_file = os.path.join(sub_dir, "sub_file.txt")
        with open(sub_file, "w", encoding="utf-8") as f:
            f.write("子目录测试内容")
        
        # 测试复制目录
        dest_dir = os.path.join(self.test_dir, "dest_dir")
        result = self.file_tool.copy(sub_dir, dest_dir)
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(dest_dir))
        self.assertTrue(os.path.exists(os.path.join(dest_dir, "sub_file.txt")))
        
        # 测试复制不存在的文件
        result = self.file_tool.copy(os.path.join(self.test_dir, "not_exist.txt"), dest_file)
        self.assertEqual(result["status"], "error")
        self.assertIn("Source path not found", result["error"])
        
        # 测试复制不允许的文件
        result = self.file_tool.copy("/etc/hosts", dest_file)
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not allowed", result["error"])
    
    def test_move(self):
        """
        测试移动文件或目录方法
        """
        # 测试移动文件
        dest_file = os.path.join(self.test_dir, "dest_file.txt")
        result = self.file_tool.move(self.test_file, dest_file)
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(dest_file))
        self.assertFalse(os.path.exists(self.test_file))
        
        # 创建子目录和文件
        sub_dir = os.path.join(self.test_dir, "sub_dir")
        os.makedirs(sub_dir)
        sub_file = os.path.join(sub_dir, "sub_file.txt")
        with open(sub_file, "w", encoding="utf-8") as f:
            f.write("子目录测试内容")
        
        # 测试移动目录
        dest_dir = os.path.join(self.test_dir, "dest_dir")
        result = self.file_tool.move(sub_dir, dest_dir)
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(dest_dir))
        self.assertTrue(os.path.exists(os.path.join(dest_dir, "sub_file.txt")))
        self.assertFalse(os.path.exists(sub_dir))
        
        # 测试移动不存在的文件
        result = self.file_tool.move(os.path.join(self.test_dir, "not_exist.txt"), dest_file)
        self.assertEqual(result["status"], "error")
        self.assertIn("Source path not found", result["error"])
        
        # 测试移动不允许的文件
        result = self.file_tool.move("/etc/hosts", dest_file)
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not allowed", result["error"])
    
    def test_get_info(self):
        """
        测试获取文件或目录信息方法
        """
        # 测试获取文件信息
        result = self.file_tool.get_info(self.test_file)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["type"], "file")
        self.assertEqual(result["name"], "test_file.txt")
        self.assertEqual(result["size"], 9)  # "测试内容" 的字节长度
        self.assertTrue("created" in result)
        self.assertTrue("modified" in result)
        
        # 测试获取目录信息
        result = self.file_tool.get_info(self.test_dir)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["type"], "directory")
        self.assertEqual(result["name"], os.path.basename(self.test_dir))
        self.assertTrue("created" in result)
        self.assertTrue("modified" in result)
        
        # 测试获取不存在的文件信息
        result = self.file_tool.get_info(os.path.join(self.test_dir, "not_exist.txt"))
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not found", result["error"])
        
        # 测试获取不允许的文件信息
        result = self.file_tool.get_info("/etc/hosts")
        self.assertEqual(result["status"], "error")
        self.assertIn("Path not allowed", result["error"])

class TestProcessTool(unittest.TestCase):
    """
    ProcessTool类测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        # 创建ProcessTool实例
        self.process_tool = ProcessTool(allowed_processes=["notepad.exe", "calc.exe"])
    
    @patch('subprocess.Popen')
    def test_start_process(self, mock_popen):
        """
        测试启动进程方法
        """
        # 模拟进程
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # 测试启动允许的进程
        result = self.process_tool.start_process("notepad.exe")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["pid"], 12345)
        mock_popen.assert_called_with(["notepad.exe"], shell=False)
        
        # 测试启动不允许的进程
        result = self.process_tool.start_process("cmd.exe")
        self.assertEqual(result["status"], "error")
        self.assertIn("Process not allowed", result["error"])
    
    @patch('psutil.Process')
    def test_stop_process(self, mock_process):
        """
        测试停止进程方法
        """
        # 模拟进程
        mock_proc = MagicMock()
        mock_proc.name.return_value = "notepad.exe"
        mock_process.return_value = mock_proc
        
        # 测试停止允许的进程
        result = self.process_tool.stop_process(12345)
        self.assertEqual(result["status"], "success")
        mock_proc.terminate.assert_called_once()
        
        # 测试进程不存在
        mock_process.side_effect = Exception("No such process")
        result = self.process_tool.stop_process(54321)
        self.assertEqual(result["status"], "error")
        self.assertIn("Process not found", result["error"])
        
        # 测试停止不允许的进程
        mock_process.side_effect = None
        mock_proc.name.return_value = "cmd.exe"
        result = self.process_tool.stop_process(12345)
        self.assertEqual(result["status"], "error")
        self.assertIn("Process not allowed", result["error"])
    
    @patch('psutil.process_iter')
    def test_list_processes(self, mock_process_iter):
        """
        测试列出进程方法
        """
        # 模拟进程列表
        mock_proc1 = MagicMock()
        mock_proc1.name.return_value = "notepad.exe"
        mock_proc1.pid = 12345
        mock_proc1.cpu_percent.return_value = 1.5
        mock_proc1.memory_info.return_value.rss = 10485760  # 10MB
        
        mock_proc2 = MagicMock()
        mock_proc2.name.return_value = "calc.exe"
        mock_proc2.pid = 54321
        mock_proc2.cpu_percent.return_value = 0.5
        mock_proc2.memory_info.return_value.rss = 5242880  # 5MB
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        # 测试列出进程
        result = self.process_tool.list_processes()
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["processes"]), 2)
        
        # 验证进程信息
        processes = {p["name"]: p for p in result["processes"]}
        self.assertIn("notepad.exe", processes)
        self.assertIn("calc.exe", processes)
        
        self.assertEqual(processes["notepad.exe"]["pid"], 12345)
        self.assertEqual(processes["notepad.exe"]["cpu"], 1.5)
        self.assertEqual(processes["notepad.exe"]["memory"], "10.0 MB")
        
        self.assertEqual(processes["calc.exe"]["pid"], 54321)
        self.assertEqual(processes["calc.exe"]["cpu"], 0.5)
        self.assertEqual(processes["calc.exe"]["memory"], "5.0 MB")
    
    @patch('psutil.Process')
    def test_get_process_info(self, mock_process):
        """
        测试获取进程信息方法
        """
        # 模拟进程
        mock_proc = MagicMock()
        mock_proc.name.return_value = "notepad.exe"
        mock_proc.pid = 12345
        mock_proc.cpu_percent.return_value = 1.5
        mock_proc.memory_info.return_value.rss = 10485760  # 10MB
        mock_proc.status.return_value = "running"
        mock_proc.create_time.return_value = 1600000000
        mock_proc.username.return_value = "user"
        mock_process.return_value = mock_proc
        
        # 测试获取进程信息
        result = self.process_tool.get_process_info(12345)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["name"], "notepad.exe")
        self.assertEqual(result["pid"], 12345)
        self.assertEqual(result["cpu"], 1.5)
        self.assertEqual(result["memory"], "10.0 MB")
        self.assertEqual(result["status"], "running")
        self.assertTrue("created" in result)
        self.assertEqual(result["user"], "user")
        
        # 测试进程不存在
        mock_process.side_effect = Exception("No such process")
        result = self.process_tool.get_process_info(54321)
        self.assertEqual(result["status"], "error")
        self.assertIn("Process not found", result["error"])
    
    @patch('subprocess.run')
    def test_execute_command(self, mock_run):
        """
        测试执行命令方法
        """
        # 模拟命令执行结果
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "命令执行成功"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # 测试执行允许的命令
        result = self.process_tool.execute_command("notepad.exe")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "命令执行成功")
        self.assertEqual(result["stderr"], "")
        mock_run.assert_called_with(["notepad.exe"], capture_output=True, text=True, shell=False)
        
        # 测试执行不允许的命令
        result = self.process_tool.execute_command("cmd.exe")
        self.assertEqual(result["status"], "error")
        self.assertIn("Command not allowed", result["error"])
        
        # 测试命令执行失败
        mock_result.returncode = 1
        mock_result.stderr = "命令执行失败"
        result = self.process_tool.execute_command("notepad.exe")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["returncode"], 1)
        self.assertEqual(result["stdout"], "命令执行成功")
        self.assertEqual(result["stderr"], "命令执行失败")

if __name__ == "__main__":
    unittest.main()