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
- **多模型支持**：基于抽象接口和工厂模式，支持多种大模型的无缝切换和扩展
- **丰富的工具模块**：
  - 文件操作：文件读写、目录管理等
  - 进程管理：启动、停止、监控进程
  - 键鼠操作：模拟鼠标点击、移动和键盘输入
  - 图像识别：查找屏幕上的图像元素
  - 屏幕截图：捕获屏幕内容
  - OCR识别：支持多种OCR后端（EasyOCR、Tesseract）
  - 延时控制：精确控制操作间隔
- **交互式执行**：支持多轮自适应执行，用户可介入决策

## 项目结构

```
LX_Agent/
├── config.py          # 配置管理模块
├── config.yaml        # 配置文件
├── main.py            # 主程序入口
├── common/            # 通用层
│   ├── __init__.py
│   ├── json_utils.py  # JSON工具函数
│   └── utils.py       # 通用工具函数
├── core/              # 核心层
│   ├── __init__.py
│   └── agent.py       # Agent 类实现
├── llm/               # 大模型接入层
│   ├── __init__.py
│   ├── base.py        # 基础抽象类
│   ├── openai.py      # OpenAI模型适配
│   ├── anthropic.py   # Anthropic模型适配
│   ├── local.py       # 本地模型适配
│   └── factory.py     # 模型工厂类
├── mcp_server/        # MCP适配层
│   ├── __init__.py
│   ├── base.py        # MCP抽象接口
│   ├── local_mcp.py   # 本地MCP适配器
│   ├── async_cloud_mcp.py # 云端MCP适配器
│   ├── factory.py     # MCP工厂类
│   └── router.py      # MCP路由器
└── tools/             # 工具层
    ├── __init__.py
    ├── file_tool.py   # 文件操作工具
    ├── process_tool.py # 进程操作工具
    ├── mouse_keyboard_tool.py # 键鼠操作工具
    ├── image_finder_tool.py # 图像查找工具
    ├── screenshot_tool.py # 屏幕截图工具
    ├── ocr_tool.py   # OCR识别工具
    ├── sleep_tool.py # 延时工具
    └── ocr_backends/ # OCR后端实现
        ├── __init__.py
        ├── base.py
        ├── easyocr_backend.py
        └── tesseract_backend.py
```

## 安装与配置

### 环境要求

- Python 版本要求：3.10+
- 操作系统：Windows、macOS、Linux

### 克隆项目

```bash
git clone https://github.com/Ikaros-521/LX_Agent.git
cd LX_Agent
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 安装OCR依赖（可选）

如果需要使用OCR功能，请安装相应的依赖：

```bash
# 安装EasyOCR
pip install easyocr

# 或安装Tesseract OCR
# Windows: 下载并安装 https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt install tesseract-ocr
# macOS: brew install tesseract

pip install pytesseract
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

在交互模式下，您可以连续输入命令并获取执行结果：

```bash
python main.py
```

### 命令行模式

直接执行单个命令并返回结果：

```bash
python main.py "打开记事本并输入Hello World"
```

### 指定配置文件

使用自定义配置文件启动：

```bash
python main.py -c custom_config.yaml
```

### 启用详细日志

开启详细日志输出：

```bash
python main.py -v
```

### 组合使用

可以组合使用上述选项：

```bash
python main.py -c custom_config.yaml -v "打开浏览器访问 https://github.com"
```

## 本地部署MCP服务

### 前置条件

- 安装Node.js环境（推荐v16+）
- 根据需要安装相应的MCP服务包

### 部署Playwright MCP服务

```bash
# 安装Playwright
npm install -g @playwright/test

# 启动Playwright MCP服务
npx @playwright/mcp@latest --port 8931
```

启动后在配置文件中添加以下配置：

```yaml
mcp:
  services:
    playwright:
      type: "cloud"
      enabled: true
      priority: 5
      url: "http://localhost:8931/mcp"
      timeout: 30
      capabilities: ["browser", "mouse", "keyboard"]
```

### 部署其他MCP服务

您可以根据需要部署其他MCP服务，如Selenium、Puppeteer等，并在配置文件中添加相应的配置。

## 扩展开发

### 添加自定义工具

在 `tools` 目录下创建新的工具模块文件（如 `custom_tool.py`），实现相应的功能接口。工具模块需要遵循以下结构：

```python
# 工具模块示例结构
class CustomTool:
    def __init__(self, config=None):
        self.config = config or {}
        # 初始化工具所需资源
        
    def get_capabilities(self):
        # 返回工具支持的能力列表
        return ["custom_capability"]
        
    async def execute(self, command, **kwargs):
        # 实现工具的执行逻辑
        # 返回执行结果
        return {"status": "success", "result": "执行结果"}
```

### 添加自定义 MCP 适配器

1. 创建自定义 MCP 适配器类，继承 `BaseMCP` 抽象类
2. 实现所有抽象方法
3. 在配置文件中添加自定义 MCP 服务配置

```python
from mcp_server.base import BaseMCP

class CustomMCPAdapter(BaseMCP):
    def __init__(self, config):
        self.config = config
        self.capabilities = config.get("capabilities", [])
        self.connected = False
        
    async def initialize(self):
        # 实现初始化逻辑
        self.connected = True
        return True
        
    async def close(self):
        # 实现关闭连接逻辑
        self.connected = False
        
    async def execute_command(self, command, **kwargs):
        # 实现命令执行逻辑
        pass
        
    async def execute_tool_call(self, tool_name, arguments):
        # 实现工具调用逻辑
        pass
        
    async def get_tools(self):
        # 返回支持的工具列表
        return []
        
    async def get_capabilities(self):
        # 返回支持的能力列表
        return self.capabilities
        
    def is_available(self):
        # 检查是否可用
        return self.connected
```

### 添加自定义大模型适配器

在 `llm` 目录下创建新的模型适配器文件（如 `custom_model.py`），继承 `BaseLLM` 类并实现相应的方法：

```python
from llm.base import BaseLLM

class CustomModelAdapter(BaseLLM):
    def __init__(self, config):
        super().__init__(config)
        # 初始化模型所需资源
        
    def analyze_command(self, command, capabilities_detail):
        # 实现命令分析逻辑
        pass
        
    async def analyze_and_generate_tool_calls(self, command, tools, **kwargs):
        # 实现工具调用生成逻辑
        pass
        
    def summarize_result(self, command, result):
        # 实现结果总结逻辑
        pass
```

## 快速开始

### 基本使用流程

1. 配置您的环境和MCP服务
2. 启动交互模式
   ```bash
   python main.py
   ```
3. 输入自然语言命令，例如：
   ```
   打开记事本
   ```
   ```
   在浏览器中搜索Python教程
   ```
   ```
   截取屏幕并保存到桌面
   ```

### 示例命令

以下是一些您可以尝试的命令示例：

- **文件操作**：`创建一个名为test.txt的文件并写入Hello World`
- **浏览器操作**：`打开Chrome浏览器并访问github.com`
- **键鼠操作**：`点击屏幕中央`
- **进程管理**：`启动计算器程序`
- **图像识别**：`查找屏幕上的关闭按钮并点击`
- **OCR识别**：`识别屏幕上的文字并复制到剪贴板`

## 常见问题

### Q: 如何解决MCP连接失败的问题？
A: 请检查MCP服务是否正常运行，并确认配置文件中的URL和端口是否正确。

### Q: 为什么某些命令无法执行？
A: 可能是因为缺少相应的MCP服务或工具模块。请检查日志输出，确保已安装所需的依赖并启动了相应的MCP服务。

### Q: 如何添加自定义工具？
A: 请参考[扩展开发](#扩展开发)部分的说明。

## 许可证

[MIT License](LICENSE)