import importlib
from typing import Optional, List, Dict, Any

class BaseOCR:
    def recognize(self, image_path: str, lang: Optional[str] = None, detailed: bool = False) -> Any:
        raise NotImplementedError("recognize 方法需要子类实现")

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
                    results.append({
                        'text': data['text'][i],
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'conf': data['conf'][i],
                        'line_num': data['line_num'][i],
                        'word_num': data['word_num'][i],
                        'block_num': data['block_num'][i],
                        'par_num': data['par_num'][i],
                        'level': data['level'][i],
                    })
            return results

class EasyOCROCR(BaseOCR):
    def __init__(self, lang: Optional[str] = None):
        try:
            import easyocr
        except ImportError:
            raise ImportError("请先安装 easyocr")
        langs = ['ch_sim', 'en']
        if lang:
            langs = lang.split('+')
        self.reader = easyocr.Reader(langs, gpu=False)
    def recognize(self, image_path: str, lang: Optional[str] = None, detailed: bool = False) -> Any:
        if not detailed:
            result = self.reader.readtext(image_path, detail=0)
            return '\n'.join(result)
        else:
            result = self.reader.readtext(image_path, detail=1)
            # [(bbox, text, conf), ...]
            detailed_result = []
            for bbox, text, conf in result:
                detailed_result.append({
                    'text': text,
                    'bbox': bbox,
                    'conf': conf
                })
            return detailed_result

class OCRFactory:
    @staticmethod
    def create(backend: str = 'tesseract', lang: Optional[str] = None) -> BaseOCR:
        if backend == 'tesseract':
            return TesseractOCR(lang=lang)
        elif backend == 'easyocr':
            return EasyOCROCR(lang=lang)
        else:
            raise ValueError(f'不支持的 OCR 后端: {backend}')

# 用法示例：
# ocr = OCRFactory.create('tesseract', lang='chi_sim+eng')
# text = ocr.recognize('test.png', detailed=True) 