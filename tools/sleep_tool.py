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