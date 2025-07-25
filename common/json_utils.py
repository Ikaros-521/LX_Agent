# JSON工具函数

import json
import numpy as np
from typing import Any


class NumpyJSONEncoder(json.JSONEncoder):
    """
    自定义JSON编码器，支持numpy数据类型的序列化
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def dumps(obj: Any, **kwargs) -> str:
    """
    将对象序列化为JSON字符串，支持numpy数据类型
    
    Args:
        obj: 要序列化的对象
        **kwargs: 其他参数传递给json.dumps
        
    Returns:
        str: 序列化后的JSON字符串
    """
    return json.dumps(obj, cls=NumpyJSONEncoder, **kwargs)


def loads(s: str, **kwargs) -> Any:
    """
    将JSON字符串反序列化为对象
    
    Args:
        s: 要反序列化的JSON字符串
        **kwargs: 其他参数传递给json.loads
        
    Returns:
        Any: 反序列化后的对象
    """
    return json.loads(s, **kwargs)