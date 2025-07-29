# LX_Agent API使用指南

本文档介绍如何使用LX_Agent的REST API接口，通过HTTP请求调用Agent的各种能力。

## 快速开始

### 1. 启动API服务器

```bash
# 使用默认配置启动
python start_api_server.py

# 指定主机和端口
python start_api_server.py --host 0.0.0.0 --port 8080

# 使用自定义配置文件
python start_api_server.py --config my_config.yaml

# 开启调试模式（自动重载）
python start_api_server.py --debug
```

### 2. 访问API文档

启动服务器后，可以通过以下地址访问交互式API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API接口概览

### 基础信息

- **基础URL**: `http://localhost:8000`
- **内容类型**: `application/json`
- **响应格式**: 统一的JSON响应格式

### 统一响应格式

所有API接口都返回统一的响应格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "session_id": "uuid-string",
  "timestamp": "2024-01-01T12:00:00"
}
```

## 接口详细说明

### 1. 系统信息接口

#### GET `/`
获取API基本信息

```bash
curl -X GET "http://localhost:8000/"
```

#### GET `/health`
健康检查

```bash
curl -X GET "http://localhost:8000/health"
```

### 2. 工具管理接口

#### GET `/tools/list`
获取所有可用工具列表

```bash
curl -X GET "http://localhost:8000/tools/list"
```

响应示例：
```json
{
  "success": true,
  "data": [
    {
      "name": "screenshot_tool",
      "description": "截图工具",
      "inputSchema": {
        "type": "object",
        "properties": {
          "filename": {"type": "string"}
        }
      },
      "mcp_name": "local"
    }
  ],
  "message": "获取到15个可用工具"
}
```

#### POST `/tools/call`
调用指定工具

```bash
curl -X POST "http://localhost:8000/tools/call" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "screenshot_tool",
    "arguments": {
      "filename": "screenshot.png"
    },
    "session_id": "optional-session-id"
  }'
```

### 3. MCP能力接口

#### GET `/mcp/capabilities`
获取MCP能力列表

```bash
curl -X GET "http://localhost:8000/mcp/capabilities"
```

#### GET `/mcp/services`
获取MCP服务列表

```bash
curl -X GET "http://localhost:8000/mcp/services"
```

### 4. LLM对话接口

#### POST `/llm/chat`
LLM对话

```bash
curl -X POST "http://localhost:8000/llm/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "你好，请介绍一下你的能力",
    "stream": false,
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### 5. 命令执行接口

#### POST `/command/execute`
执行智能体命令（核心功能）

```bash
curl -X POST "http://localhost:8000/command/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "帮我截个屏并保存到桌面",
    "session_id": "my-session-123",
    "auto_continue": false,
    "max_steps": 10
  }'
```

参数说明：
- `command`: 要执行的自然语言命令
- `session_id`: 可选，用于会话管理和上下文保持
- `auto_continue`: 是否自动继续执行，false时每步都会等待确认
- `max_steps`: 最大执行步数，防止无限循环

### 6. 会话管理接口

#### POST `/session/manage`
会话管理

```bash
# 清空会话历史
curl -X POST "http://localhost:8000/session/manage" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session-123",
    "clear_history": true
  }'

# 获取会话信息
curl -X POST "http://localhost:8000/session/manage" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session-123"
  }'

# 获取所有会话
curl -X POST "http://localhost:8000/session/manage" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### DELETE `/session/{session_id}`
删除会话

```bash
curl -X DELETE "http://localhost:8000/session/my-session-123"
```

## 使用示例

### Python客户端示例

```python
import requests
import json

class LXAgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def execute_command(self, command, auto_continue=False, max_steps=10):
        """执行命令"""
        url = f"{self.base_url}/command/execute"
        data = {
            "command": command,
            "auto_continue": auto_continue,
            "max_steps": max_steps
        }
        if self.session_id:
            data["session_id"] = self.session_id
        
        response = requests.post(url, json=data)
        result = response.json()
        
        # 保存会话ID
        if result.get("session_id"):
            self.session_id = result["session_id"]
        
        return result
    
    def call_tool(self, tool_name, arguments):
        """调用工具"""
        url = f"{self.base_url}/tools/call"
        data = {
            "tool_name": tool_name,
            "arguments": arguments
        }
        if self.session_id:
            data["session_id"] = self.session_id
        
        response = requests.post(url, json=data)
        return response.json()
    
    def chat_with_llm(self, prompt, stream=False):
        """与LLM对话"""
        url = f"{self.base_url}/llm/chat"
        data = {
            "prompt": prompt,
            "stream": stream
        }
        
        response = requests.post(url, json=data)
        return response.json()
    
    def get_tools(self):
        """获取可用工具"""
        url = f"{self.base_url}/tools/list"
        response = requests.get(url)
        return response.json()

# 使用示例
client = LXAgentClient()

# 执行命令
result = client.execute_command("帮我截个屏")
print(json.dumps(result, indent=2, ensure_ascii=False))

# 调用工具
result = client.call_tool("screenshot_tool", {"filename": "test.png"})
print(json.dumps(result, indent=2, ensure_ascii=False))

# LLM对话
result = client.chat_with_llm("你好")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### JavaScript客户端示例

```javascript
class LXAgentClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.sessionId = null;
    }
    
    async executeCommand(command, autoContinue = false, maxSteps = 10) {
        const url = `${this.baseUrl}/command/execute`;
        const data = {
            command: command,
            auto_continue: autoContinue,
            max_steps: maxSteps
        };
        
        if (this.sessionId) {
            data.session_id = this.sessionId;
        }
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        // 保存会话ID
        if (result.session_id) {
            this.sessionId = result.session_id;
        }
        
        return result;
    }
    
    async callTool(toolName, arguments) {
        const url = `${this.baseUrl}/tools/call`;
        const data = {
            tool_name: toolName,
            arguments: arguments
        };
        
        if (this.sessionId) {
            data.session_id = this.sessionId;
        }
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        return await response.json();
    }
    
    async getTools() {
        const url = `${this.baseUrl}/tools/list`;
        const response = await fetch(url);
        return await response.json();
    }
}

// 使用示例
const client = new LXAgentClient();

// 执行命令
client.executeCommand('帮我截个屏').then(result => {
    console.log(JSON.stringify(result, null, 2));
});
```

## 错误处理

### 常见错误码

- `503`: Agent未初始化
- `404`: 会话不存在
- `500`: 内部服务器错误

### 错误响应格式

```json
{
  "detail": "错误详细信息"
}
```

## 最佳实践

### 1. 会话管理

- 使用会话ID来保持上下文
- 定期清理不需要的会话
- 长时间不活跃的会话会被自动清理

### 2. 错误处理

- 始终检查响应的`success`字段
- 处理网络超时和连接错误
- 对于长时间运行的命令，考虑设置合适的超时时间

### 3. 性能优化

- 对于简单操作，直接使用工具调用接口
- 对于复杂任务，使用命令执行接口
- 合理设置`max_steps`参数避免无限循环

### 4. 安全考虑

- 在生产环境中限制CORS域名
- 对敏感操作进行身份验证
- 监控API调用频率和异常

## 故障排除

### 1. 服务器无法启动

- 检查配置文件是否存在
- 确认端口未被占用
- 查看日志文件获取详细错误信息

### 2. Agent初始化失败

- 检查LLM配置是否正确
- 确认MCP服务是否可用
- 查看Agent日志获取详细信息

### 3. 工具调用失败

- 确认工具名称和参数正确
- 检查工具是否在可用列表中
- 查看MCP服务状态

## 更多信息

- [项目文档](../README.md)
- [配置指南](../config.yaml)
- [扩展开发指南](扩展开发指南.md)