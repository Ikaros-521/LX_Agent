#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LX_Agent API服务器启动脚本

使用方法:
    python start_api_server.py [--host HOST] [--port PORT] [--config CONFIG]

示例:
    python start_api_server.py --host 0.0.0.0 --port 8000
    python start_api_server.py --config custom_config.yaml
"""

import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import uvicorn
    from loguru import logger
except ImportError as e:
    print(f"缺少必要的依赖: {e}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="LX_Agent API服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  启动默认服务器:
    python start_api_server.py
    
  指定主机和端口:
    python start_api_server.py --host 0.0.0.0 --port 8080
    
  使用自定义配置文件:
    python start_api_server.py --config my_config.yaml
    
  开启调试模式:
    python start_api_server.py --debug
        """
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务器主机地址 (默认: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器端口 (默认: 8000)"
    )
    
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式 (自动重载)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数 (默认: 1, 注意: 多进程模式下会话管理可能有问题)"
    )
    
    return parser.parse_args()


def setup_logging(log_level: str):
    """设置日志"""
    # 确保logs目录存在
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 配置loguru
    logger.remove()  # 移除默认处理器
    
    # 控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 文件输出
    logger.add(
        logs_dir / "api_server.log",
        level=log_level,
        rotation="10 MB",
        retention=5,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )


def check_config_file(config_path: str):
    """检查配置文件是否存在"""
    config_file = Path(config_path)
    if not config_file.exists():
        logger.error(f"配置文件不存在: {config_file.absolute()}")
        logger.info("请确保配置文件存在，或使用 --config 参数指定正确的配置文件路径")
        return False
    
    logger.info(f"使用配置文件: {config_file.absolute()}")
    return True


def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    logger.info("="*60)
    logger.info("LX_Agent API服务器启动中...")
    logger.info("="*60)
    
    # 检查配置文件
    if not check_config_file(args.config):
        sys.exit(1)
    
    # 设置环境变量，让api_server.py知道配置文件路径
    os.environ["LX_AGENT_CONFIG"] = args.config
    
    # 显示启动信息
    logger.info(f"服务器地址: http://{args.host}:{args.port}")
    logger.info(f"配置文件: {args.config}")
    logger.info(f"调试模式: {'开启' if args.debug else '关闭'}")
    logger.info(f"日志级别: {args.log_level}")
    logger.info(f"工作进程: {args.workers}")
    
    if args.workers > 1:
        logger.warning("多进程模式下，会话管理功能可能无法正常工作")
    
    logger.info("-"*60)
    logger.info("API文档地址:")
    logger.info(f"  Swagger UI: http://{args.host}:{args.port}/docs")
    logger.info(f"  ReDoc: http://{args.host}:{args.port}/redoc")
    logger.info("-"*60)
    
    try:
        # 启动服务器
        uvicorn.run(
            "api_server:app",
            host=args.host,
            port=args.port,
            reload=args.debug,
            log_level=args.log_level.lower(),
            workers=args.workers if not args.debug else 1,  # 调试模式下强制单进程
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)
    finally:
        logger.info("LX_Agent API服务器已关闭")


if __name__ == "__main__":
    main()