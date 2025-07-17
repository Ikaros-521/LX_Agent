# 主程序入口

import os
import sys
import argparse

from config import Config
from loguru import logger
from core.agent import Agent

def parse_args():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="LX_Agent - 多MCP支持的智能代理")
    parser.add_argument(
        "-c", "--config",
        help="配置文件路径",
        default="config.yaml"
    )
    parser.add_argument(
        "-v", "--verbose",
        help="启用详细日志",
        action="store_true"
    )
    parser.add_argument(
        "command",
        help="要执行的命令",
        nargs="*"
    )
    
    return parser.parse_args()

def main():
    """
    主程序入口
    """
    logger.info("主程序启动")
    agent = Agent(config)
    
    try:
        logger.info("初始化Agent...")
        if not agent.initialize():
            logger.error("Agent初始化失败")
            return 1
            
        if not args.command:
            # logger.info("进入交互模式")
            interactive_mode(agent)
        else:
            command = " ".join(args.command)
            logger.info(f"执行命令行参数命令: {command}")
            execute_command(agent, command)
            
        logger.info("主程序正常结束")
        return 0
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        return 0
    except Exception as e:
        logger.error(f"主程序异常: {str(e)}")
        return 1
    finally:
        logger.info("关闭Agent")
        agent.close()


def interactive_mode(agent: Agent):
    logger.info("进入交互模式")
    print("LX_Agent 交互模式 (输入 'exit' 或 'quit' 退出)", flush=True)
    print("可用MCP服务:", flush=True)
    
    available_mcps = agent.mcp_router.get_available_mcps()
    logger.info(f"检测到可用MCP服务: {len(available_mcps)} 个")
    for name, mcp in available_mcps:
        capabilities = mcp.get_capabilities()
        logger.debug(f"MCP: {name}, 能力: {capabilities}")
        print(f"  - {name}: {', '.join(capabilities)}", flush=True)
    
    context_config = agent.config.get_context_config()
    max_rounds = context_config.get("max_rounds", 5)
    history = []
    while True:
        try:
            command = input("\n> ")
            command = command.strip()
            logger.debug(f"用户输入: {command}")
            if command.lower() in ["exit", "quit"]:
                logger.info("用户退出交互模式")
                break
            if not command:
                continue
            # 新版：多轮人机协同主循环
            agent.execute_interactive(command, history)
            if len(history) >= max_rounds:
                history.pop(0)
            history.append({"command": command})
        except KeyboardInterrupt:
            logger.info("交互模式被用户中断")
            print("\nInterrupted", flush=True)
            break
        except Exception as e:
            logger.error(f"交互模式异常: {str(e)}")


def execute_command(agent: Agent, command: str, history=None):
    logger.info(f"开始执行命令: {command}")
    if history is None:
        history = []
    logger.debug(f"传入历史: {history}")
    # 新版：多轮人机协同主循环
    agent.execute_interactive(command, history)

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    # 加载配置
    config = Config(args.config)
    
    log_config = config.get_logger_config()
    log_file = log_config.get("file", "logs/agent.log")
    log_level = "DEBUG" if args.verbose else log_config.get("level", "INFO")
    rotation = log_config.get("max_size", 10485760)  # 支持文件轮转
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get("format", "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.add(log_file, level=log_level, rotation=rotation, retention=backup_count, format=log_format)

    sys.exit(main())