#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
运行所有单元测试的脚本
"""

import os
import sys
import unittest
import argparse

def run_tests(test_pattern=None, verbose=False):
    """
    运行单元测试
    
    Args:
        test_pattern: 测试模式，用于筛选测试用例
        verbose: 是否显示详细信息
    
    Returns:
        测试结果
    """
    # 设置测试目录
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    
    # 添加项目根目录到路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 创建测试加载器
    loader = unittest.TestLoader()
    
    # 加载测试用例
    if test_pattern:
        # 加载指定模式的测试用例
        suite = loader.discover(test_dir, pattern=f"test_{test_pattern}.py")
    else:
        # 加载所有测试用例
        suite = loader.discover(test_dir, pattern="test_*.py")
    
    # 创建测试运行器
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    
    # 运行测试
    result = runner.run(suite)
    
    return result

def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行LX_Agent单元测试")
    parser.add_argument("-t", "--test", help="指定要运行的测试模块（例如：agent, config, mcp_router）")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细测试信息")
    args = parser.parse_args()
    
    # 运行测试
    result = run_tests(args.test, args.verbose)
    
    # 输出测试结果摘要
    print("\n测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    # 设置退出码
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()