# 日志模块

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

def setup_logging(config: Dict[str, Any] = None) -> None:
    """
    设置日志
    
    Args:
        config: 日志配置，默认为None
    """
    if not config:
        config = {}
        
    # 获取日志配置
    log_level = config.get("level", "INFO")
    log_format = config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_file = config.get("file", "logs/agent.log")
    max_size = config.get("max_size", 10 * 1024 * 1024)  # 默认10MB
    backup_count = config.get("backup_count", 5)
    
    # 创建日志目录
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 设置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # 清除已有的处理器
    for handler in root_logger.handlers[::]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(log_format)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info("Logging setup complete")