# FastAPI服务器 - 提供LX_Agent的API接口

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from config import Config
from core.agent import Agent


# 全局变量
agent: Optional[Agent] = None
active_sessions: Dict[str, Dict] = {}  # 存储活跃的会话


# Pydantic模型定义
class ToolCallRequest(BaseModel):
    """工具调用请求"""
    tool_name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    session_id: Optional[str] = Field(None, description="会话ID，用于上下文管理")


class CommandRequest(BaseModel):
    """命令执行请求"""
    command: str = Field(..., description="要执行的命令")
    session_id: Optional[str] = Field(None, description="会话ID，用于上下文管理")
    auto_continue: bool = Field(False, description="是否自动继续执行")
    max_steps: int = Field(10, description="最大执行步数")


class LLMRequest(BaseModel):
    """LLM对话请求"""
    prompt: str = Field(..., description="输入提示")
    stream: bool = Field(False, description="是否流式响应")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")


class SessionRequest(BaseModel):
    """会话管理请求"""
    session_id: Optional[str] = Field(None, description="会话ID")
    clear_history: bool = Field(False, description="是否清空历史")


class ApiResponse(BaseModel):
    """API响应基础模型"""
    success: bool = Field(..., description="是否成功")
    data: Any = Field(None, description="响应数据")
    message: str = Field("", description="响应消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global agent
    
    # 启动时初始化Agent
    logger.info("正在初始化LX_Agent...")
    config_path = os.getenv("LX_AGENT_CONFIG", "config.yaml")
    logger.info(f"使用配置文件: {config_path}")
    config = Config(config_path)
    agent = Agent(config)
    
    if not await agent.initialize():
        logger.error("Agent初始化失败")
        raise RuntimeError("Agent初始化失败")
    
    logger.info("LX_Agent初始化成功")
    yield
    
    # 关闭时清理资源
    logger.info("正在关闭LX_Agent...")
    if agent:
        await agent.close()
    logger.info("LX_Agent已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="LX_Agent API",
    description="LX_Agent的REST API接口，提供工具调用、MCP能力和LLM对话功能",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_or_create_session(session_id: Optional[str] = None) -> str:
    """获取或创建会话"""
    if session_id and session_id in active_sessions:
        return session_id
    
    new_session_id = session_id or str(uuid.uuid4())
    active_sessions[new_session_id] = {
        "created_at": datetime.now(),
        "history": [],
        "last_activity": datetime.now()
    }
    return new_session_id


def update_session_activity(session_id: str):
    """更新会话活动时间"""
    if session_id in active_sessions:
        active_sessions[session_id]["last_activity"] = datetime.now()


@app.get("/", response_model=ApiResponse)
async def root():
    """根路径，返回API信息"""
    return ApiResponse(
        success=True,
        data={
            "name": "LX_Agent API",
            "version": "1.0.0",
            "description": "LX_Agent的REST API接口",
            "endpoints": [
                "/tools/list",
                "/tools/call",
                "/mcp/capabilities",
                "/mcp/services",
                "/llm/chat",
                "/command/execute",
                "/session/manage"
            ]
        },
        message="LX_Agent API服务正常运行"
    )


@app.get("/health", response_model=ApiResponse)
async def health_check():
    """健康检查"""
    if not agent or not agent.initialized:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    
    return ApiResponse(
        success=True,
        data={"status": "healthy", "agent_initialized": agent.initialized},
        message="服务健康"
    )


@app.get("/tools/list", response_model=ApiResponse)
async def list_tools():
    """获取所有可用工具列表"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    
    try:
        tools = await agent.mcp_router.get_all_tools()
        return ApiResponse(
            success=True,
            data=tools,
            message=f"获取到{len(tools)}个可用工具"
        )
    except Exception as e:
        logger.error(f"获取工具列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


@app.post("/tools/call", response_model=ApiResponse)
async def call_tool(request: ToolCallRequest):
    """调用指定工具"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    
    session_id = get_or_create_session(request.session_id)
    update_session_activity(session_id)
    
    try:
        result = await agent.mcp_router.execute_tool_call(
            request.tool_name, 
            request.arguments
        )
        
        # 记录到会话历史
        active_sessions[session_id]["history"].append({
            "type": "tool_call",
            "tool_name": request.tool_name,
            "arguments": request.arguments,
            "result": result,
            "timestamp": datetime.now()
        })
        
        return ApiResponse(
            success=True,
            data=result,
            message=f"工具{request.tool_name}执行完成",
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"工具调用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"工具调用失败: {str(e)}")


@app.get("/mcp/capabilities", response_model=ApiResponse)
async def get_mcp_capabilities():
    """获取MCP能力列表"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    
    try:
        available_mcps = await agent.mcp_router.get_available_mcps()
        capabilities = {}
        
        for name, mcp in available_mcps:
            mcp_capabilities = await mcp.get_capabilities()
            capabilities[name] = mcp_capabilities
        
        return ApiResponse(
            success=True,
            data=capabilities,
            message=f"获取到{len(capabilities)}个MCP服务的能力信息"
        )
    except Exception as e:
        logger.error(f"获取MCP能力失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取MCP能力失败: {str(e)}")


@app.get("/mcp/services", response_model=ApiResponse)
async def get_mcp_services():
    """获取MCP服务列表"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    
    try:
        available_mcps = await agent.mcp_router.get_available_mcps()
        services = []
        
        for name, mcp in available_mcps:
            capabilities = await mcp.get_capabilities()
            services.append({
                "name": name,
                "capabilities": capabilities,
                "available": await mcp.is_available()
            })
        
        return ApiResponse(
            success=True,
            data=services,
            message=f"获取到{len(services)}个MCP服务"
        )
    except Exception as e:
        logger.error(f"获取MCP服务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取MCP服务失败: {str(e)}")


@app.post("/llm/chat", response_model=ApiResponse)
async def llm_chat(request: LLMRequest):
    """LLM对话接口"""
    if not agent or not agent.llm:
        raise HTTPException(status_code=503, detail="LLM未初始化")
    
    try:
        kwargs = {}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        
        if request.stream:
            # 流式响应需要特殊处理
            response_chunks = []
            for chunk in agent.llm.generate_stream(request.prompt, **kwargs):
                response_chunks.append(chunk)
            
            response = "".join(response_chunks)
        else:
            response = agent.llm.generate(request.prompt, **kwargs)
        
        return ApiResponse(
            success=True,
            data={"response": response, "stream": request.stream},
            message="LLM响应生成完成"
        )
    except Exception as e:
        logger.error(f"LLM对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM对话失败: {str(e)}")


@app.post("/command/execute", response_model=ApiResponse)
async def execute_command(request: CommandRequest):
    """执行命令（智能体交互式执行）"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    
    session_id = get_or_create_session(request.session_id)
    update_session_activity(session_id)
    
    try:
        # 获取会话历史
        session_history = active_sessions[session_id]["history"]
        
        # 转换为Agent期望的历史格式
        agent_history = []
        for item in session_history:
            if item["type"] == "command_execution":
                agent_history.extend(item.get("execution_history", []))
        
        # 执行命令
        result = await agent.execute_interactive(
            command=request.command,
            history=agent_history,
            max_steps=request.max_steps,
            auto_continue=request.auto_continue
        )
        
        # 记录到会话历史
        active_sessions[session_id]["history"].append({
            "type": "command_execution",
            "command": request.command,
            "execution_history": result.get("results", []),
            "final_summary": result.get("final_summary"),
            "status": result.get("status"),
            "timestamp": datetime.now()
        })
        
        return ApiResponse(
            success=True,
            data=result,
            message="命令执行完成",
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"命令执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"命令执行失败: {str(e)}")


@app.post("/session/manage", response_model=ApiResponse)
async def manage_session(request: SessionRequest):
    """会话管理"""
    session_id = request.session_id
    
    if request.clear_history:
        if session_id and session_id in active_sessions:
            active_sessions[session_id]["history"] = []
            update_session_activity(session_id)
            return ApiResponse(
                success=True,
                data={"action": "clear_history"},
                message="会话历史已清空",
                session_id=session_id
            )
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    
    # 如果没有指定操作，返回会话信息
    if session_id:
        if session_id in active_sessions:
            session_info = active_sessions[session_id].copy()
            # 转换datetime为字符串
            session_info["created_at"] = session_info["created_at"].isoformat()
            session_info["last_activity"] = session_info["last_activity"].isoformat()
            
            return ApiResponse(
                success=True,
                data=session_info,
                message="获取会话信息成功",
                session_id=session_id
            )
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        # 返回所有活跃会话
        sessions_info = {}
        for sid, session in active_sessions.items():
            sessions_info[sid] = {
                "created_at": session["created_at"].isoformat(),
                "last_activity": session["last_activity"].isoformat(),
                "history_count": len(session["history"])
            }
        
        return ApiResponse(
            success=True,
            data=sessions_info,
            message=f"获取到{len(sessions_info)}个活跃会话"
        )


@app.delete("/session/{session_id}", response_model=ApiResponse)
async def delete_session(session_id: str):
    """删除会话"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return ApiResponse(
            success=True,
            data={"action": "delete_session"},
            message="会话已删除"
        )
    else:
        raise HTTPException(status_code=404, detail="会话不存在")


if __name__ == "__main__":
    import uvicorn
    
    # 配置日志
    logger.add(
        "logs/api_server.log",
        level="INFO",
        rotation="10 MB",
        retention=5,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 启动服务器
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 生产环境建议设为False
        log_level="info"
    )