import importlib
from typing import Optional, List, Dict, Any

from common.json_utils import dumps, loads
from tools.ocr_backends.base import BaseOCR
from tools.ocr_backends.easyocr_backend import EasyOCROCR
from tools.ocr_backends.tesseract_backend import TesseractOCR


class TesseractOCR(BaseOCR):
    def __init__(self, lang: Optional[str] = None):
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError("请先安装 pytesseract 和 pillow")
        self.pytesseract = pytesseract
        self.Image = Image
        self.lang = lang or 'chi_sim+eng'
    def recognize(self, image_path: str, lang: Optional[str] = None, detailed: bool = False) -> Any:
        img = self.Image.open(image_path)
        if not detailed:
            return self.pytesseract.image_to_string(img, lang=lang or self.lang)
        else:
            data = self.pytesseract.image_to_data(img, lang=lang or self.lang, output_type=self.pytesseract.Output.DICT)
            results = []
            n = len(data['text'])
            for i in range(n):
                if int(data['conf'][i]) > 0 and data['text'][i].strip():
                    # 确保所有值都是Python原生类型
                    results.append({
                        'text': str(data['text'][i]),
                        'left': int(data['left'][i]),
                        'top': int(data['top'][i]),
                        'width': int(data['width'][i]),
                        'height': int(data['height'][i]),
                        'conf': float(data['conf'][i]),
                        'line_num': int(data['line_num'][i]),
                        'word_num': int(data['word_num'][i]),
                        'block_num': int(data['block_num'][i]),
                        'par_num': int(data['par_num'][i]),
                        'level': int(data['level'][i]),
                    })
            # 确保结果可以被JSON序列化
            return loads(dumps(results))

class OCRFactory:
    @staticmethod
    def create(backend: str = 'easyocr', lang: Optional[str] = None) -> BaseOCR:
        if backend == 'tesseract':
            return TesseractOCR(lang=lang)
        elif backend == 'easyocr':
            return EasyOCROCR(lang=lang)
        else:
            raise ValueError(f'不支持的 OCR 后端: {backend}')

# 用法示例：
# ocr = OCRFactory.create('tesseract', lang='chi_sim+eng')
# text = ocr.recognize('test.png', detailed=True)

def get_capabilities():
    return ["ocr_tool"]

def get_tools():
    return [
        {
            "name": "ocr",
            "description": "OCR识别图片中的文字（支持多后端和多语言，lang如'ch_sim'、'en'、'ch_sim+en'）。detailed=True时返回每个文本的坐标、置信度等结构化信息，detailed=False时仅返回纯文本。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "图片文件路径"},
                    "backend": {"type": "string", "description": "OCR后端，可选：tesseract、easyocr", "default": "easyocr"},
                    "lang": {"type": "string", "description": "OCR语言，如'ch_sim'、'en'、'ch_sim+en'，可选"},
                    "detailed": {"type": "boolean", "description": "是否返回详细结构化数据和坐标，True时返回每个文本的坐标、置信度等信息，False时仅返回纯文本", "default": False}
                },
                "required": ["image_path"]
            }
        }
    ]

def call_tool(name, arguments):
    if name == "ocr":
        import os
        from common.json_utils import dumps, loads
        image_path = arguments.get("image_path")
        backend = arguments.get("backend", "easyocr")
        lang = arguments.get("lang")
        detailed = arguments.get("detailed", False)
        if not image_path:
            return {"status": "error", "error": "缺少图片路径"}
        # 路径修正：相对路径转绝对路径
        if not os.path.isabs(image_path):
            image_path = os.path.abspath(image_path)
        try:
            ocr = OCRFactory.create(backend, lang=lang)
            result = ocr.recognize(image_path, lang=lang, detailed=detailed)
            # 使用自定义JSON编码器处理可能包含numpy数据类型的结果
            # 先序列化再反序列化，确保所有numpy类型都被转换为Python原生类型
            result_serializable = loads(dumps(result))
            if detailed:
                return {"status": "success", "result": result_serializable}
            else:
                return {"status": "success", "text": result_serializable}
        except BaseException as e:
            return {"status": "error", "error": str(e)}
    else:
        return {"status": "error", "error": f"Unknown tool: {name}"}