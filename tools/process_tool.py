# 进程操作工具

import os
import sys
import time
import signal
from loguru import logger
import platform
import subprocess
from typing import Dict, Any, List, Optional

from common.utils import run_command, is_windows



class ProcessTool:
    """
    进程操作工具类
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化进程工具
        
        Args:
            config: 工具配置
        """
        self.config = config
        self.processes: Dict[int, subprocess.Popen] = {}
    
    def start_process(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        启动进程
        
        Args:
            command: 要执行的命令
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 启动进程
            process = subprocess.Popen(
                command,
                shell=is_windows(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **kwargs
            )
            
            # 保存进程
            self.processes[process.pid] = process
            
            return {
                "status": "success",
                "pid": process.pid,
                "command": command
            }
        except BaseException as e:
            logger.error(f"Failed to start process: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def stop_process(self, pid: int) -> Dict[str, Any]:
        """
        停止进程
        
        Args:
            pid: 进程ID
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 检查进程是否存在
            if pid not in self.processes:
                # 尝试通过系统命令停止进程
                if is_windows():
                    returncode, stdout, stderr = run_command(f"taskkill /F /PID {pid}")
                else:
                    returncode, stdout, stderr = run_command(f"kill -9 {pid}")
                    
                if returncode != 0:
                    return {
                        "status": "error",
                        "error": f"Process {pid} not found"
                    }
            else:
                # 停止进程
                process = self.processes[pid]
                
                if is_windows():
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
                    
                # 等待进程结束
                process.wait(timeout=5)
                
                # 如果进程仍在运行，强制结束
                if process.poll() is None:
                    if is_windows():
                        process.kill()
                    else:
                        process.send_signal(signal.SIGKILL)
                    
                # 从进程列表中移除
                del self.processes[pid]
            
            return {
                "status": "success",
                "pid": pid
            }
        except BaseException as e:
            logger.error(f"Failed to stop process {pid}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def list_processes(self) -> Dict[str, Any]:
        """
        列出进程
        
        Returns:
            Dict[str, Any]: 进程列表
        """
        try:
            # 获取进程列表
            if is_windows():
                returncode, stdout, stderr = run_command("tasklist /FO CSV /NH")
                
                if returncode != 0:
                    return {
                        "status": "error",
                        "error": stderr
                    }
                    
                # 解析进程列表
                processes = []
                for line in stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                        
                    # 解析CSV格式
                    parts = line.strip('"').split('","')
                    if len(parts) >= 2:
                        name = parts[0]
                        pid = int(parts[1])
                        processes.append({
                            "name": name,
                            "pid": pid
                        })
            else:
                returncode, stdout, stderr = run_command("ps -e -o pid,comm")
                
                if returncode != 0:
                    return {
                        "status": "error",
                        "error": stderr
                    }
                    
                # 解析进程列表
                processes = []
                lines = stdout.strip().split("\n")
                for line in lines[1:]:  # 跳过标题行
                    parts = line.strip().split(None, 1)
                    if len(parts) >= 2:
                        pid = int(parts[0])
                        name = parts[1]
                        processes.append({
                            "name": name,
                            "pid": pid
                        })
            
            return {
                "status": "success",
                "processes": processes
            }
        except BaseException as e:
            logger.error(f"Failed to list processes: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_process_info(self, pid: int) -> Dict[str, Any]:
        """
        获取进程信息
        
        Args:
            pid: 进程ID
            
        Returns:
            Dict[str, Any]: 进程信息
        """
        try:
            # 检查进程是否存在
            if pid in self.processes:
                process = self.processes[pid]
                
                return {
                    "status": "success",
                    "pid": pid,
                    "running": process.poll() is None,
                    "returncode": process.returncode if process.poll() is not None else None
                }
            
            # 通过系统命令获取进程信息
            if is_windows():
                returncode, stdout, stderr = run_command(f"tasklist /FI \"PID eq {pid}\" /FO CSV /NH")
                
                if returncode != 0 or "INFO: No tasks" in stderr:
                    return {
                        "status": "error",
                        "error": f"Process {pid} not found"
                    }
                    
                # 解析进程信息
                if stdout.strip():
                    parts = stdout.strip('"').split('","')
                    if len(parts) >= 2:
                        name = parts[0]
                        return {
                            "status": "success",
                            "pid": pid,
                            "name": name,
                            "running": True
                        }
            else:
                returncode, stdout, stderr = run_command(f"ps -p {pid} -o pid,comm")
                
                if returncode != 0 or not stdout.strip():
                    return {
                        "status": "error",
                        "error": f"Process {pid} not found"
                    }
                    
                # 解析进程信息
                lines = stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].strip().split(None, 1)
                    if len(parts) >= 2:
                        name = parts[1]
                        return {
                            "status": "success",
                            "pid": pid,
                            "name": name,
                            "running": True
                        }
            
            return {
                "status": "error",
                "error": f"Process {pid} not found"
            }
        except BaseException as e:
            logger.error(f"Failed to get process info for {pid}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        执行命令并等待结果
        
        Args:
            command: 要执行的命令
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            # 执行命令
            returncode, stdout, stderr = run_command(command, **kwargs)
            
            return {
                "status": "success" if returncode == 0 else "error",
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "command": command
            }
        except BaseException as e:
            logger.error(f"Failed to execute command: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "command": command
            }