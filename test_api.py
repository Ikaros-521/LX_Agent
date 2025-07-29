#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LX_Agent API测试脚本

用于测试API服务器的各项功能是否正常工作。

使用方法:
    python test_api.py [--host HOST] [--port PORT]

示例:
    python test_api.py
    python test_api.py --host localhost --port 8080
"""

import argparse
import json
import time
import requests
from typing import Dict, Any


class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = None
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "data": data,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if not success and data:
            print(f"   详细信息: {data}")
    
    def test_health_check(self):
        """测试健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("健康检查", True, "服务器运行正常")
                    return True
                else:
                    self.log_test("健康检查", False, "服务器响应异常", data)
            else:
                self.log_test("健康检查", False, f"HTTP状态码: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("健康检查", False, f"连接失败: {str(e)}")
        return False
    
    def test_root_endpoint(self):
        """测试根端点"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("根端点", True, "API信息获取成功")
                    return True
                else:
                    self.log_test("根端点", False, "响应格式异常", data)
            else:
                self.log_test("根端点", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("根端点", False, f"请求失败: {str(e)}")
        return False
    
    def test_list_tools(self):
        """测试工具列表"""
        try:
            response = requests.get(f"{self.base_url}/tools/list", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and isinstance(data.get("data"), list):
                    tool_count = len(data["data"])
                    self.log_test("工具列表", True, f"获取到{tool_count}个工具")
                    return data["data"]
                else:
                    self.log_test("工具列表", False, "响应格式异常", data)
            else:
                self.log_test("工具列表", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("工具列表", False, f"请求失败: {str(e)}")
        return None
    
    def test_mcp_capabilities(self):
        """测试MCP能力"""
        try:
            response = requests.get(f"{self.base_url}/mcp/capabilities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    capabilities = data.get("data", {})
                    mcp_count = len(capabilities)
                    self.log_test("MCP能力", True, f"获取到{mcp_count}个MCP服务的能力")
                    return capabilities
                else:
                    self.log_test("MCP能力", False, "响应格式异常", data)
            else:
                self.log_test("MCP能力", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("MCP能力", False, f"请求失败: {str(e)}")
        return None
    
    def test_mcp_services(self):
        """测试MCP服务"""
        try:
            response = requests.get(f"{self.base_url}/mcp/services", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and isinstance(data.get("data"), list):
                    service_count = len(data["data"])
                    self.log_test("MCP服务", True, f"获取到{service_count}个MCP服务")
                    return data["data"]
                else:
                    self.log_test("MCP服务", False, "响应格式异常", data)
            else:
                self.log_test("MCP服务", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("MCP服务", False, f"请求失败: {str(e)}")
        return None
    
    def test_llm_chat(self):
        """测试LLM对话"""
        try:
            payload = {
                "prompt": "你好，请简单介绍一下你自己",
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 100
            }
            response = requests.post(
                f"{self.base_url}/llm/chat", 
                json=payload, 
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response_text = data.get("data", {}).get("response", "")
                    self.log_test("LLM对话", True, f"LLM响应长度: {len(response_text)}字符")
                    return True
                else:
                    self.log_test("LLM对话", False, "响应格式异常", data)
            else:
                self.log_test("LLM对话", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("LLM对话", False, f"请求失败: {str(e)}")
        return False
    
    def test_tool_call(self, tools):
        """测试工具调用"""
        if not tools:
            self.log_test("工具调用", False, "没有可用工具")
            return False
        
        # 寻找一个简单的工具进行测试
        test_tool = None
        for tool in tools:
            if tool.get("name") == "sleep_tool":
                test_tool = tool
                break
        
        if not test_tool:
            # 如果没有sleep_tool，使用第一个工具
            test_tool = tools[0]
        
        try:
            payload = {
                "tool_name": test_tool["name"],
                "arguments": {"seconds": 0.1} if test_tool["name"] == "sleep_tool" else {}
            }
            response = requests.post(
                f"{self.base_url}/tools/call", 
                json=payload, 
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.session_id = data.get("session_id")  # 保存会话ID
                    self.log_test("工具调用", True, f"成功调用工具: {test_tool['name']}")
                    return True
                else:
                    self.log_test("工具调用", False, "工具执行失败", data)
            else:
                self.log_test("工具调用", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("工具调用", False, f"请求失败: {str(e)}")
        return False
    
    def test_session_management(self):
        """测试会话管理"""
        if not self.session_id:
            self.log_test("会话管理", False, "没有可用的会话ID")
            return False
        
        try:
            # 测试获取会话信息
            payload = {"session_id": self.session_id}
            response = requests.post(
                f"{self.base_url}/session/manage", 
                json=payload, 
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("会话管理", True, "会话信息获取成功")
                    return True
                else:
                    self.log_test("会话管理", False, "会话信息获取失败", data)
            else:
                self.log_test("会话管理", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("会话管理", False, f"请求失败: {str(e)}")
        return False
    
    def test_command_execution(self):
        """测试命令执行（简单命令）"""
        try:
            payload = {
                "command": "等待0.1秒",
                "auto_continue": True,
                "max_steps": 3
            }
            response = requests.post(
                f"{self.base_url}/command/execute", 
                json=payload, 
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results = data.get("data", {}).get("results", [])
                    self.log_test("命令执行", True, f"命令执行完成，共{len(results)}步")
                    return True
                else:
                    self.log_test("命令执行", False, "命令执行失败", data)
            else:
                self.log_test("命令执行", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("命令执行", False, f"请求失败: {str(e)}")
        return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("LX_Agent API 功能测试")
        print(f"测试目标: {self.base_url}")
        print("="*60)
        
        # 基础连接测试
        if not self.test_health_check():
            print("\n❌ 健康检查失败，停止后续测试")
            return False
        
        self.test_root_endpoint()
        
        # 功能测试
        tools = self.test_list_tools()
        self.test_mcp_capabilities()
        self.test_mcp_services()
        
        # LLM测试（可能失败，取决于配置）
        self.test_llm_chat()
        
        # 工具调用测试
        self.test_tool_call(tools)
        
        # 会话管理测试
        self.test_session_management()
        
        # 命令执行测试
        self.test_command_execution()
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print("\n" + "="*60)
        return failed_tests == 0


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="LX_Agent API测试脚本")
    parser.add_argument(
        "--host",
        default="localhost",
        help="API服务器主机地址 (默认: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="请求超时时间（秒） (默认: 30)"
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    base_url = f"http://{args.host}:{args.port}"
    
    print(f"开始测试 LX_Agent API: {base_url}")
    print(f"请确保API服务器已启动...\n")
    
    tester = APITester(base_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！API服务器工作正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查API服务器配置和状态。")
        return 1


if __name__ == "__main__":
    exit(main())