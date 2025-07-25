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