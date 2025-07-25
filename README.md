# 洛曦Agent - 多MCP支持的智能代理

## 项目简介

LX_Agent 是一个支持多个 MCP（Machine Control Protocol）服务同时接入的智能代理系统。它能够根据不同的路由策略（能力匹配、优先级优先、负载均衡）选择合适的 MCP 服务执行命令，并提供故障转移机制，确保高可用性。

## 主要特性

- **多 MCP 支持**：同时接入多个 MCP 服务，包括本地 MCP 和云端 MCP
- **智能路由策略**：
  - 能力匹配：根据命令所需能力选择合适的 MCP
  - 优先级优先：根据 MCP 优先级选择
  - 负载均衡：在多个 MCP 之间分配负载
- **故障转移机制**：当首选 MCP 执行失败时，自动尝试备选 MCP
- **可扩展架构**：支持通过配置文件添加自定义 MCP 服务
- **丰富的工具模块**：提供文件操作、进程管理等工具

## 项目结构

```
LX_Agent/
├── config.py          # 配置管理模块
├── config.yaml        # 配置文件
├── main.py            # 主程序入口
├── common/            # 通用层
│   ├── __init__.py
│   └── utils.py       # 通用工具函数
├── core/              # 核心层
│   ├── __init__.py
│   └── agent.py       # Agent 类实现
├── mcp/               # MCP 适配层
│   ├── __init__.py
│   ├── base.py        # MCP 抽象接口
│   ├── local_mcp.py   # 本地 MCP 适配器
│   ├── async_cloud_mcp.py   # 云端 MCP 适配器
│   ├── factory.py     # MCP 工厂类
│   └── router.py      # MCP 路由器
└── tools/             # 工具层
    ├── __init__.py
    ├── file_tool.py   # 文件操作工具
    └── process_tool.py # 进程操作工具
```

## 安装与配置

### 环境要求

Python 版本要求：3.10+  

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置文件

编辑 `config.yaml` 文件，配置 MCP 服务和其他设置：

```yaml
# MCP配置
mcp:
  # 路由策略: capability_match(能力匹配), priority_first(优先级优先), load_balance(负载均衡)
  routing_strategy: "capability_match"
  # MCP服务配置
  services:
    # 本地MCP
    local:
      type: "local"
      enabled: true
      priority: 10
      capabilities: ["file", "process", "shell"]
    # 云端MCP
    cloud:
      type: "cloud"
      enabled: true
      priority: 5
      url: "https://example.com/mcp/api"
      api_key: "YOUR_CLOUD_MCP_API_KEY"
      timeout: 30
      capabilities: ["file", "browser", "mouse", "keyboard", "process", "shell"]
```

## 使用方法

### 交互模式

```bash
python main.py
```

## 本地部署MCP服务

安装Nodejs环境  

启动命令例如playwright服务：`npx @playwright/mcp@latest --port 8931`，启动后在yaml配置文件中添加配置即可，API地址为`http://localhost:8931/mcp`  

## 扩展开发

### 本地工具开发

在 `mcp_server/tools` 文件夹下创建 某个`_tool.py`文件，会自动搜索这个工具注册并获取其内部定义的能力。

### 云端工具开发

在 `mcp_server/async_cloud_mcp.py` 中添加新的工具类，并在 `AsyncCloudMCPAdapter` 的 `_get_tools` 方法中注册该工具。

## 许可证

[MIT License](LICENSE)