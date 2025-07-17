from tools.ocr_tool import BaseOCR

class EasyOCROCR(BaseOCR):
    def __init__(self, lang=None):
        try:
            import easyocr
        except ImportError:
            raise ImportError("请先安装 easyocr")
        langs = ['ch_sim', 'en']
        if lang:
            langs = lang.split('+')
        self.reader = easyocr.Reader(langs, gpu=False)
    def recognize(self, image_path: str, lang=None, detailed: bool = False):
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