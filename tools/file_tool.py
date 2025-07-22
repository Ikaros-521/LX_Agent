# 文件操作工具

import os
import shutil
from loguru import logger
from typing import Dict, Any, List, Optional

from common.utils import ensure_dir, is_path_allowed, get_file_type, format_size



class FileTool:
    """
    文件操作工具类
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件工具
        
        Args:
            config: 工具配置
        """
        self.config = config
        self.allowed_paths = config.get("allowed_paths", [])
        self.denied_paths = config.get("denied_paths", [])
    
    def check_path(self, path: str) -> bool:
        """
        检查路径是否被允许访问
        
        Args:
            path: 要检查的路径
            
        Returns:
            bool: 路径是否被允许访问
        """
        return is_path_allowed(path, self.allowed_paths, self.denied_paths)
    
    def list_directory(self, path: str) -> Dict[str, Any]:
        """
        列出目录内容
        
        Args:
            path: 目录路径
            
        Returns:
            Dict[str, Any]: 目录内容
        """
        # 检查路径是否被允许
        if not self.check_path(path):
            return {
                "status": "error",
                "error": "Path not allowed"
            }
        
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                return {
                    "status": "error",
                    "error": "Path not exist"
                }
                
            # 检查路径是否为目录
            if not os.path.isdir(path):
                return {
                    "status": "error",
                    "error": "Path is not a directory"
                }
                
            # 列出目录内容
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_type = "directory" if os.path.isdir(item_path) else "file"
                item_size = 0 if item_type == "directory" else os.path.getsize(item_path)
                
                items.append({
                    "name": item,
                    "type": item_type,
                    "size": item_size,
                    "size_formatted": format_size(item_size),
                    "modified": os.path.getmtime(item_path)
                })
                
            return {
                "status": "success",
                "path": path,
                "items": items
            }
        except BaseException as e:
            logger.error(f"Failed to list directory {path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """
        读取文件内容
        
        Args:
            path: 文件路径
            
        Returns:
            Dict[str, Any]: 文件内容
        """
        # 检查路径是否被允许
        if not self.check_path(path):
            return {
                "status": "error",
                "error": "Path not allowed"
            }
        
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                return {
                    "status": "error",
                    "error": "File not exist"
                }
                
            # 检查路径是否为文件
            if not os.path.isfile(path):
                return {
                    "status": "error",
                    "error": "Path is not a file"
                }
                
            # 读取文件内容
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            return {
                "status": "success",
                "path": path,
                "content": content,
                "size": os.path.getsize(path),
                "size_formatted": format_size(os.path.getsize(path))
            }
        except BaseException as e:
            logger.error(f"Failed to read file {path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        写入文件内容
        
        Args:
            path: 文件路径
            content: 文件内容
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        # 检查路径是否被允许
        if not self.check_path(path):
            return {
                "status": "error",
                "error": "Path not allowed"
            }
        
        try:
            # 确保目录存在
            dir_path = os.path.dirname(path)
            if not ensure_dir(dir_path):
                return {
                    "status": "error",
                    "error": f"Failed to create directory {dir_path}"
                }
                
            # 写入文件内容
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return {
                "status": "success",
                "path": path,
                "size": len(content),
                "size_formatted": format_size(len(content))
            }
        except BaseException as e:
            logger.error(f"Failed to write file {path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """
        删除文件或目录
        
        Args:
            path: 文件或目录路径
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        # 检查路径是否被允许
        if not self.check_path(path):
            return {
                "status": "error",
                "error": "Path not allowed"
            }
        
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                return {
                    "status": "error",
                    "error": "Path not exist"
                }
                
            # 删除文件或目录
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
                
            return {
                "status": "success",
                "path": path
            }
        except BaseException as e:
            logger.error(f"Failed to delete {path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def copy_file(self, src_path: str, dst_path: str) -> Dict[str, Any]:
        """
        复制文件或目录
        
        Args:
            src_path: 源路径
            dst_path: 目标路径
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        # 检查路径是否被允许
        if not self.check_path(src_path) or not self.check_path(dst_path):
            return {
                "status": "error",
                "error": "Path not allowed"
            }
        
        try:
            # 检查源路径是否存在
            if not os.path.exists(src_path):
                return {
                    "status": "error",
                    "error": "Source path not exist"
                }
                
            # 确保目标目录存在
            dst_dir = os.path.dirname(dst_path)
            if not ensure_dir(dst_dir):
                return {
                    "status": "error",
                    "error": f"Failed to create directory {dst_dir}"
                }
                
            # 复制文件或目录
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
                
            return {
                "status": "success",
                "src_path": src_path,
                "dst_path": dst_path
            }
        except BaseException as e:
            logger.error(f"Failed to copy {src_path} to {dst_path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def move_file(self, src_path: str, dst_path: str) -> Dict[str, Any]:
        """
        移动文件或目录
        
        Args:
            src_path: 源路径
            dst_path: 目标路径
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        # 检查路径是否被允许
        if not self.check_path(src_path) or not self.check_path(dst_path):
            return {
                "status": "error",
                "error": "Path not allowed"
            }
        
        try:
            # 检查源路径是否存在
            if not os.path.exists(src_path):
                return {
                    "status": "error",
                    "error": "Source path not exist"
                }
                
            # 确保目标目录存在
            dst_dir = os.path.dirname(dst_path)
            if not ensure_dir(dst_dir):
                return {
                    "status": "error",
                    "error": f"Failed to create directory {dst_dir}"
                }
                
            # 移动文件或目录
            shutil.move(src_path, dst_path)
                
            return {
                "status": "success",
                "src_path": src_path,
                "dst_path": dst_path
            }
        except BaseException as e:
            logger.error(f"Failed to move {src_path} to {dst_path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        获取文件或目录信息
        
        Args:
            path: 文件或目录路径
            
        Returns:
            Dict[str, Any]: 文件或目录信息
        """
        # 检查路径是否被允许
        if not self.check_path(path):
            return {
                "status": "error",
                "error": "Path not allowed"
            }
        
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                return {
                    "status": "error",
                    "error": "Path not exist"
                }
                
            # 获取文件或目录信息
            file_type = get_file_type(path)
            file_size = 0 if file_type == "directory" else os.path.getsize(path)
            
            return {
                "status": "success",
                "path": path,
                "type": file_type,
                "size": file_size,
                "size_formatted": format_size(file_size),
                "created": os.path.getctime(path),
                "modified": os.path.getmtime(path),
                "accessed": os.path.getatime(path)
            }
        except BaseException as e:
            logger.error(f"Failed to get info for {path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }