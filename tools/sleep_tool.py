import asyncio

async def sleep_tool(ms: int = None, s: float = None):
    """
    异步睡眠指定时间
    :param ms: 毫秒
    :param s: 秒
    :return: {'status': 'success', 'slept': 秒数}
    """
    if ms is not None:
        seconds = ms / 1000.0
    elif s is not None:
        seconds = float(s)
    else:
        return {'status': 'error', 'error': '必须指定 ms 或 s 参数'}
    await asyncio.sleep(seconds)
    return {'status': 'success', 'slept': seconds}

def get_capabilities():
    return ["sleep_tool"]

def get_tools():
    return [
        {
            "name": "sleep",
            "description": "异步睡眠指定时间（ms或s）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ms": {"type": "integer", "description": "毫秒，可选"},
                    "s": {"type": "number", "description": "秒，可选"}
                },
                "anyOf": [
                    {"required": ["ms"]},
                    {"required": ["s"]}
                ]
            }
        }
    ]

def call_tool(name, arguments):
    if name == "sleep":
        import asyncio
        ms = arguments.get("ms")
        s = arguments.get("s")
        coro = sleep_tool(ms=ms, s=s)
        if asyncio.iscoroutine(coro):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)
        else:
            return coro
    else:
        return {"status": "error", "error": f"Unknown tool: {name}"} 