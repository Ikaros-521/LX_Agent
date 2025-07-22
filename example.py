# 使用示例

import os
import sys

from config import Config
from loguru import logger
from core.agent import Agent

def main():
    """
    示例主函数
    """
    # 加载配置
    config = Config()
    
    # 创建Agent
    agent = Agent(config)
    
    # 初始化Agent
    if not agent.initialize():
        logger.error("Failed to initialize Agent")
        return 1
    
    try:
        # 示例1：执行简单命令
        print("\n示例1：执行简单命令")
        result = agent.execute("echo Hello, LX_Agent!")
        print(f"执行结果: {result}")
        
        # 示例2：分析命令并执行
        print("\n示例2：分析命令并执行")
        command = "列出当前目录文件"
        print(f"命令: {command}")
        capabilities = agent.analyze_command(command)
        print(f"分析得到的能力: {capabilities}")
        result = agent.execute_with_analysis(command)
        print(f"执行结果: {result}")
        
        # 示例3：指定所需能力
        print("\n示例3：指定所需能力")
        result = agent.execute("打开浏览器访问百度", ["browser"])
        print(f"执行结果: {result}")
        
        return 0
    except KeyboardInterrupt:
        print("\n操作被中断")
        return 0
    except BaseException as e:
        logger.error(f"Error: {str(e)}")
        return 1
    finally:
        # 关闭Agent
        agent.close()

if __name__ == "__main__":
    sys.exit(main())