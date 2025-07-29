# LX_Agent API 服务器

本项目提供了一个基于 FastAPI 的 REST API 接口，将 LX_Agent 的本地工具能力、MCP 能力和 LLM 能力暴露为 Web API，方便外部系统调用。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

#### Windows
```cmd
# 使用批处理脚本（推荐）
start_server.bat

# 或直接使用 Python
python start_api_server.py
```

#### Linux/macOS
```bash
# 使用 shell 脚本（推荐）
./start_server.sh

# 或直接使用 Python
python3 start_api_server.py
```

### 3. 访问 API 文档

启动成功后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 API 端点概览

### 系统信息
- `GET /` - 获取 API 基本信息
- `GET /health` - 健康检查

### 工具管理
- `GET /tools/list` - 获取所有可用工具列表
- `POST /tools/call` - 调用指定工具

### MCP 能力
- `GET /mcp/capabilities` - 获取 MCP 能力信息
- `GET /mcp/services` - 获取 MCP 服务列表

### LLM 对话
- `POST /llm/chat` - 与 LLM 进行对话

### 命令执行
- `POST /command/execute` - 执行自然语言命令

### 会话管理
- `POST /session/manage` - 管理执行会话

## 🛠️ 配置选项

### 启动参数

```bash
python start_api_server.py [选项]

选项:
  --host HOST        服务器主机地址 (默认: 0.0.0.0)
  --port PORT        服务器端口 (默认: 8000)
  --config CONFIG    配置文件路径 (默认: config.yaml)
  --workers WORKERS  工作进程数 (默认: 1)
  --log-level LEVEL  日志级别 (默认: info)
  --debug            启用调试模式
```

### 环境变量

- `LX_AGENT_CONFIG`: 配置文件路径（默认: config.yaml）

## 📝 使用示例

### Python 客户端示例

```python
import requests

# API 基地址
base_url = "http://localhost:8000"

# 1. 健康检查
response = requests.get(f"{base_url}/health")
print(response.json())

# 2. 获取工具列表
response = requests.get(f"{base_url}/tools/list")
tools = response.json()["data"]
print(f"可用工具数量: {len(tools)}")

# 3. LLM 对话
payload = {
    "prompt": "你好，请介绍一下你自己",
    "stream": False,
    "temperature": 0.7
}
response = requests.post(f"{base_url}/llm/chat", json=payload)
print(response.json()["data"]["response"])

# 4. 执行命令
payload = {
    "command": "获取当前时间",
    "auto_continue": True,
    "max_steps": 5
}
response = requests.post(f"{base_url}/command/execute", json=payload)
results = response.json()["data"]["results"]
print(f"执行步骤: {len(results)}")
```

### JavaScript 客户端示例

```javascript
const baseUrl = 'http://localhost:8000';

// 1. 健康检查
fetch(`${baseUrl}/health`)
  .then(response => response.json())
  .then(data => console.log(data));

// 2. LLM 对话
fetch(`${baseUrl}/llm/chat`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    prompt: '你好，请介绍一下你自己',
    stream: false,
    temperature: 0.7
  })
})
.then(response => response.json())
.then(data => console.log(data.data.response));

// 3. 执行命令
fetch(`${baseUrl}/command/execute`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    command: '获取当前时间',
    auto_continue: true,
    max_steps: 5
  })
})
.then(response => response.json())
.then(data => console.log(`执行步骤: ${data.data.results.length}`));
```

## 🧪 测试

### 运行 API 测试

```bash
# 确保 API 服务器已启动，然后运行测试
python test_api.py

# 指定服务器地址和端口
python test_api.py --host localhost --port 8080
```

测试脚本会自动检查所有 API 端点的功能是否正常。

## 📊 响应格式

所有 API 响应都遵循统一的 JSON 格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-string"
}
```

### 成功响应
- `success`: true
- `data`: 具体的响应数据
- `message`: 成功消息

### 错误响应
- `success`: false
- `error`: 错误详情
- `message`: 错误消息

## 🔧 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/macOS
   lsof -i :8000
   ```

2. **依赖缺失**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置文件错误**
   - 检查 `config.yaml` 文件格式
   - 确保所有必需的配置项都已设置

4. **权限问题**
   - 确保有读取配置文件的权限
   - 确保有绑定指定端口的权限

### 日志查看

服务器日志会显示详细的错误信息，包括：
- 启动过程
- 请求处理
- 错误堆栈

## 🔒 安全注意事项

1. **生产环境部署**
   - 不要在生产环境中使用 `--debug` 模式
   - 考虑使用反向代理（如 Nginx）
   - 配置适当的防火墙规则

2. **API 访问控制**
   - 当前版本未包含身份验证
   - 建议在受信任的网络环境中使用
   - 可以通过反向代理添加身份验证

3. **敏感信息**
   - 不要在日志中记录敏感信息
   - 确保配置文件的安全性

## 📚 更多信息

- 详细的 API 文档：访问 `/docs` 端点
- 配置说明：查看 `config.yaml` 文件
- 工具开发：参考 `tools/` 目录下的示例
- MCP 集成：查看 `mcp_server/` 目录

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目采用 MIT 许可证。