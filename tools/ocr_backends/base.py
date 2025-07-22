from typing import Optional, Any

class BaseOCR:
    def recognize(self, image_path: str, lang: Optional[str] = None, detailed: bool = False) -> Any:
        raise NotImplementedError("recognize 方法需要子类实现")