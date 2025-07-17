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
    # 创建Agent
    agent = Agent(config)
    
    try:
        # 初始化Agent
        if not agent.initialize():
            logger.error("Failed to initialize Agent")
            return 1
            
        # 如果没有提供命令，进入交互模式
        if not args.command:
            interactive_mode(agent)
        else:
            # 执行命令
            command = " ".join(args.command)
            execute_command(agent, command)
            
        return 0
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
    finally:
        # 关闭Agent
        agent.close()

def interactive_mode(agent: Agent):
    """
    交互模式
    
    Args:
        agent: Agent实例
    """
    print("LX_Agent 交互模式 (输入 'exit' 或 'quit' 退出)")
    print("可用MCP服务:")
    
    available_mcps = agent.mcp_router.get_available_mcps()
    for name, mcp in available_mcps:
        capabilities = mcp.get_capabilities()
        print(f"  - {name}: {', '.join(capabilities)}")
    
    while True:
        try:
            # 获取用户输入
            command = input("\n> ")
            command = command.strip()
            
            # 检查退出命令
            if command.lower() in ["exit", "quit"]:
                break
                
            # 空命令
            if not command:
                continue
                
            # 执行命令
            execute_command(agent, command)
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")

def execute_command(agent: Agent, command: str):
    """
    执行命令
    
    Args:
        agent: Agent实例
        command: 要执行的命令
    """
    # 分析命令并执行
    result = agent.execute_with_analysis(command)

    # 处理需要二次确认的shell命令
    if result.get("status") == "need_confirm":
        print(result["message"])
        confirm = input("> ").strip().lower()
        if confirm in ("确认", "yes", "y"):
            exec_result = agent.execute(result["shell_cmd"], ["shell"])
            result = exec_result
        else:
            print("已取消执行。"); return

    # 处理结果
    if result.get("status") == "success":
        # 输出结果
        if "stdout" in result:
            print(result["stdout"])
        if "stderr" in result and result["stderr"]:
            print(f"错误: {result['stderr']}")
        
        # 如果使用了备选MCP，输出提示
        if result.get("fallback"):
            print(f"注意: 使用备选MCP服务 {result.get('mcp_name')} 执行命令")
        
        # 使用LLM总结结果
        summary = agent.summarize_result(command, result)
        print(f"\n总结: {summary}")
    else:
        # 输出错误信息
        print(f"执行失败: {result.get('error', '')}，{result.get('stderr', '')}")

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