# fastmcp Agent API 文档

本文档详细说明了 fastmcp Agent 项目提供的 API 接口，包括 REST API 和 WebSocket API，用于与外部系统集成。

## 一、概述

fastmcp Agent 提供了两种类型的 API：

1. **REST API**：用于同步请求-响应模式的交互，适合简单的命令执行和状态查询。
2. **WebSocket API**：用于实时双向通信，适合需要持续更新状态的场景，如长时间运行的任务监控。

所有 API 都需要进行身份验证，支持基于 API 密钥和 JWT 令牌的认证方式。

## 二、认证

### 1. API 密钥认证

在请求头中添加 API 密钥：

```
Authorization: Bearer YOUR_API_KEY
```

### 2. JWT 认证

首先获取 JWT 令牌：

```http
POST /api/auth/token
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

然后在请求头中使用令牌：

```
Authorization: Bearer YOUR_JWT_TOKEN
```

## 三、REST API

### 1. 会话管理

#### 创建会话

```http
POST /api/sessions
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "llm": "openai",  // 可选，默认使用配置中的默认值
  "mcp": "local",   // 可选，默认使用配置中的默认值
  "metadata": {      // 可选，会话元数据
    "user_id": "user123",
    "source": "web_app"
  }
}
```

响应：

```json
{
  "session_id": "sess_123456789",
  "created_at": "2023-06-15T10:30:00Z",
  "status": "active",
  "llm": "openai",
  "mcp": "local"
}
```

#### 获取会话列表

```http
GET /api/sessions
Authorization: Bearer YOUR_API_KEY
```

响应：

```json
{
  "sessions": [
    {
      "session_id": "sess_123456789",
      "created_at": "2023-06-15T10:30:00Z",
      "status": "active",
      "llm": "openai",
      "mcp": "local"
    },
    {
      "session_id": "sess_987654321",
      "created_at": "2023-06-14T15:45:00Z",
      "status": "inactive",
      "llm": "anthropic",
      "mcp": "cloud"
    }
  ],
  "total": 2
}
```

#### 获取会话详情

```http
GET /api/sessions/{session_id}
Authorization: Bearer YOUR_API_KEY
```

响应：

```json
{
  "session_id": "sess_123456789",
  "created_at": "2023-06-15T10:30:00Z",
  "updated_at": "2023-06-15T10:35:00Z",
  "status": "active",
  "llm": "openai",
  "mcp": "local",
  "metadata": {
    "user_id": "user123",
    "source": "web_app"
  },
  "message_count": 5
}
```

#### 结束会话

```http
DELETE /api/sessions/{session_id}
Authorization: Bearer YOUR_API_KEY
```

响应：

```json
{
  "success": true,
  "message": "Session terminated successfully"
}
```

### 2. 消息交互

#### 发送指令

```http
POST /api/sessions/{session_id}/messages
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "content": "打开浏览器并访问 https://www.example.com",
  "stream": false  // 可选，是否流式返回结果
}
```

响应：

```json
{
  "message_id": "msg_123456789",
  "created_at": "2023-06-15T10:40:00Z",
  "role": "user",
  "content": "打开浏览器并访问 https://www.example.com"
}
```

#### 获取响应

```http
GET /api/sessions/{session_id}/messages/{message_id}/response
Authorization: Bearer YOUR_API_KEY
```

响应：

```json
{
  "message_id": "msg_987654321",
  "created_at": "2023-06-15T10:40:05Z",
  "role": "assistant",
  "content": "已成功打开浏览器并访问 https://www.example.com",
  "status": "completed",
  "actions": [
    {
      "type": "browser.open",
      "params": {
        "url": "https://www.example.com"
      },
      "status": "success"
    }
  ]
}
```

#### 获取会话历史

```http
GET /api/sessions/{session_id}/messages
Authorization: Bearer YOUR_API_KEY
```

响应：

```json
{
  "messages": [
    {
      "message_id": "msg_123456789",
      "created_at": "2023-06-15T10:40:00Z",
      "role": "user",
      "content": "打开浏览器并访问 https://www.example.com"
    },
    {
      "message_id": "msg_987654321",
      "created_at": "2023-06-15T10:40:05Z",
      "role": "assistant",
      "content": "已成功打开浏览器并访问 https://www.example.com",
      "status": "completed",
      "actions": [
        {
          "type": "browser.open",
          "params": {
            "url": "https://www.example.com"
          },
          "status": "success"
        }
      ]
    }
  ],
  "total": 2
}
```

### 3. 工具操作

#### 获取可用工具列表

```http
GET /api/tools
Authorization: Bearer YOUR_API_KEY
```

响应：

```json
{
  "tools": [
    {
      "name": "file.list",
      "description": "List files in a directory",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Directory path"
          }
        },
        "required": ["path"]
      }
    },
    {
      "name": "browser.open",
      "description": "Open a URL in the browser",
      "parameters": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string",
            "description": "URL to open"
          }
        },
        "required": ["url"]
      }
    }
    // 更多工具...
  ]
}
```

#### 直接调用工具

```http
POST /api/tools/{tool_name}
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "session_id": "sess_123456789",  // 可选，关联到特定会话
  "params": {                      // 工具参数
    "path": "/home/user/documents"
  }
}
```

响应：

```json
{
  "tool": "file.list",
  "status": "success",
  "result": {
    "files": [
      {
        "name": "document1.txt",
        "type": "file",
        "size": 1024,
        "modified": "2023-06-10T15:30:00Z"
      },
      {
        "name": "images",
        "type": "directory",
        "modified": "2023-06-12T09:45:00Z"
      }
    ]
  }
}
```

### 4. 系统状态

#### 获取系统状态

```http
GET /api/status
Authorization: Bearer YOUR_API_KEY
```

响应：

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 86400,  // 秒
  "active_sessions": 5,
  "llm_status": {
    "openai": "connected",
    "anthropic": "connected",
    "local": "disconnected"
  },
  "mcp_status": {
    "local": "connected",
    "cloud": "connected"
  }
}
```

## 四、WebSocket API

### 1. 建立连接

```
WS /api/ws?token=YOUR_API_KEY
```

或者使用 JWT 令牌：

```
WS /api/ws?token=YOUR_JWT_TOKEN
```

### 2. 消息格式

所有 WebSocket 消息都使用 JSON 格式，包含 `type` 字段指定消息类型。

#### 客户端到服务器的消息类型

##### 创建会话

```json
{
  "type": "create_session",
  "data": {
    "llm": "openai",
    "mcp": "local",
    "metadata": {
      "user_id": "user123",
      "source": "web_app"
    }
  }
}
```

##### 发送指令

```json
{
  "type": "send_message",
  "data": {
    "session_id": "sess_123456789",
    "content": "打开浏览器并访问 https://www.example.com"
  }
}
```

##### 调用工具

```json
{
  "type": "call_tool",
  "data": {
    "session_id": "sess_123456789",  // 可选
    "tool": "file.list",
    "params": {
      "path": "/home/user/documents"
    }
  }
}
```

##### 结束会话

```json
{
  "type": "end_session",
  "data": {
    "session_id": "sess_123456789"
  }
}
```

#### 服务器到客户端的消息类型

##### 会话创建响应

```json
{
  "type": "session_created",
  "data": {
    "session_id": "sess_123456789",
    "created_at": "2023-06-15T10:30:00Z",
    "status": "active",
    "llm": "openai",
    "mcp": "local"
  }
}
```

##### 消息响应

```json
{
  "type": "message_received",
  "data": {
    "session_id": "sess_123456789",
    "message_id": "msg_123456789",
    "created_at": "2023-06-15T10:40:00Z",
    "role": "user",
    "content": "打开浏览器并访问 https://www.example.com"
  }
}
```

##### 助手响应

```json
{
  "type": "assistant_response",
  "data": {
    "session_id": "sess_123456789",
    "message_id": "msg_987654321",
    "created_at": "2023-06-15T10:40:05Z",
    "role": "assistant",
    "content": "已成功打开浏览器并访问 https://www.example.com",
    "status": "completed",
    "actions": [
      {
        "type": "browser.open",
        "params": {
          "url": "https://www.example.com"
        },
        "status": "success"
      }
    ]
  }
}
```

##### 工具调用响应

```json
{
  "type": "tool_result",
  "data": {
    "session_id": "sess_123456789",  // 如果有关联会话
    "tool": "file.list",
    "status": "success",
    "result": {
      "files": [
        {
          "name": "document1.txt",
          "type": "file",
          "size": 1024,
          "modified": "2023-06-10T15:30:00Z"
        },
        {
          "name": "images",
          "type": "directory",
          "modified": "2023-06-12T09:45:00Z"
        }
      ]
    }
  }
}
```

##### 进度更新

```json
{
  "type": "progress_update",
  "data": {
    "session_id": "sess_123456789",
    "message_id": "msg_987654321",
    "progress": 50,  // 百分比
    "status": "processing",
    "current_action": {
      "type": "browser.open",
      "params": {
        "url": "https://www.example.com"
      },
      "status": "in_progress"
    }
  }
}
```

##### 错误消息

```json
{
  "type": "error",
  "data": {
    "code": "invalid_session",
    "message": "Session not found or expired",
    "request_id": "req_123456789"
  }
}
```

## 五、错误处理

所有 API 错误都会返回适当的 HTTP 状态码和 JSON 格式的错误信息：

```json
{
  "error": {
    "code": "invalid_session",
    "message": "Session not found or expired",
    "request_id": "req_123456789"
  }
}
```

### 常见错误代码

| 错误代码 | 描述 |
|---------|------|
| `invalid_auth` | 认证失败 |
| `invalid_session` | 会话不存在或已过期 |
| `invalid_message` | 消息格式错误 |
| `tool_not_found` | 工具不存在 |
| `tool_execution_failed` | 工具执行失败 |
| `llm_error` | 大模型调用错误 |
| `mcp_error` | MCP服务错误 |
| `rate_limit_exceeded` | 超出请求频率限制 |

## 六、限流策略

API 请求受到以下限流策略的约束：

- 认证 API：每 IP 每分钟 10 次请求
- 会话管理 API：每用户每分钟 60 次请求
- 消息 API：每会话每分钟 120 次请求
- 工具调用 API：每会话每分钟 300 次请求

超出限制时，API 将返回 429 Too Many Requests 状态码。

## 七、安全建议

1. 使用 HTTPS 加密所有 API 通信
2. 定期轮换 API 密钥
3. 为 JWT 令牌设置合理的过期时间
4. 实施 IP 白名单限制
5. 监控异常的 API 调用模式

## 八、示例代码

### Python 示例

```python
import requests
import json
import websocket
import threading

# REST API 示例
def rest_api_example():
    api_key = "YOUR_API_KEY"
    base_url = "https://api.example.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 创建会话
    session_response = requests.post(
        f"{base_url}/api/sessions",
        headers=headers,
        json={
            "llm": "openai",
            "mcp": "local"
        }
    )
    session_data = session_response.json()
    session_id = session_data["session_id"]
    
    # 发送指令
    message_response = requests.post(
        f"{base_url}/api/sessions/{session_id}/messages",
        headers=headers,
        json={
            "content": "打开浏览器并访问 https://www.example.com"
        }
    )
    message_data = message_response.json()
    message_id = message_data["message_id"]
    
    # 获取响应
    response = requests.get(
        f"{base_url}/api/sessions/{session_id}/messages/{message_id}/response",
        headers=headers
    )
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 结束会话
    requests.delete(
        f"{base_url}/api/sessions/{session_id}",
        headers=headers
    )

# WebSocket API 示例
def on_message(ws, message):
    data = json.loads(message)
    print(f"Received: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data["type"] == "session_created":
        session_id = data["data"]["session_id"]
        # 发送指令
        ws.send(json.dumps({
            "type": "send_message",
            "data": {
                "session_id": session_id,
                "content": "打开浏览器并访问 https://www.example.com"
            }
        }))

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Connection opened")
    # 创建会话
    ws.send(json.dumps({
        "type": "create_session",
        "data": {
            "llm": "openai",
            "mcp": "local"
        }
    }))

def websocket_example():
    api_key = "YOUR_API_KEY"
    ws_url = f"wss://api.example.com/api/ws?token={api_key}"
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # 保持主线程运行
    try:
        while True:
            pass
    except KeyboardInterrupt:
        ws.close()

if __name__ == "__main__":
    # 选择一个示例运行
    rest_api_example()
    # websocket_example()
```

### JavaScript 示例

```javascript
// REST API 示例
async function restApiExample() {
  const apiKey = "YOUR_API_KEY";
  const baseUrl = "https://api.example.com";
  const headers = {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json"
  };
  
  // 创建会话
  const sessionResponse = await fetch(`${baseUrl}/api/sessions`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      llm: "openai",
      mcp: "local"
    })
  });
  const sessionData = await sessionResponse.json();
  const sessionId = sessionData.session_id;
  
  // 发送指令
  const messageResponse = await fetch(`${baseUrl}/api/sessions/${sessionId}/messages`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      content: "打开浏览器并访问 https://www.example.com"
    })
  });
  const messageData = await messageResponse.json();
  const messageId = messageData.message_id;
  
  // 获取响应
  const response = await fetch(`${baseUrl}/api/sessions/${sessionId}/messages/${messageId}/response`, {
    method: "GET",
    headers
  });
  console.log(await response.json());
  
  // 结束会话
  await fetch(`${baseUrl}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers
  });
}

// WebSocket API 示例
function websocketExample() {
  const apiKey = "YOUR_API_KEY";
  const wsUrl = `wss://api.example.com/api/ws?token=${apiKey}`;
  
  const ws = new WebSocket(wsUrl);
  let sessionId = null;
  
  ws.onopen = () => {
    console.log("Connection opened");
    // 创建会话
    ws.send(JSON.stringify({
      type: "create_session",
      data: {
        llm: "openai",
        mcp: "local"
      }
    }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Received:", data);
    
    if (data.type === "session_created") {
      sessionId = data.data.session_id;
      // 发送指令
      ws.send(JSON.stringify({
        type: "send_message",
        data: {
          session_id: sessionId,
          content: "打开浏览器并访问 https://www.example.com"
        }
      }));
    }
  };
  
  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };
  
  ws.onclose = () => {
    console.log("Connection closed");
  };
  
  // 清理函数
  return () => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  };
}

// 选择一个示例运行
restApiExample().catch(console.error);
// const cleanup = websocketExample();
// setTimeout(cleanup, 60000); // 60秒后关闭连接
```

## 九、更新日志

### v1.0.0 (2023-06-01)

- 初始版本发布
- 支持基本的会话管理和消息交互
- 提供 REST API 和 WebSocket API

### v1.1.0 (2023-07-15)

- 添加工具直接调用 API
- 改进错误处理和限流策略
- 增加 JWT 认证支持

### v1.2.0 (2023-09-01)

- 添加流式响应支持
- 优化 WebSocket 连接稳定性
- 增加会话元数据支持

---

如有任何问题或建议，请联系我们的技术支持团队。