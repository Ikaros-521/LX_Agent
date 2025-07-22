from tools.ocr_tool import BaseOCR

LANG_MAP_TESSERACT_TO_EASYOCR = {
    'chi_sim': 'ch_sim',
    'chi_tra': 'ch_tra',
    'zh_sim': 'ch_sim',
    'eng': 'en',
    'jpn': 'ja',
    'kor': 'ko',
    # 可扩展
}

class EasyOCROCR(BaseOCR):
    def __init__(self, lang=None):
        try:
            import easyocr
        except ImportError:
            raise ImportError("请先安装 easyocr")
        langs = ['ch_sim', 'en']
        if lang:
            # 统一类型
            if isinstance(lang, str):
                if ',' in lang:
                    langs = [l.strip() for l in lang.split(',')]
                elif '+' in lang:
                    langs = [l.strip() for l in lang.split('+')]
                else:
                    langs = [lang.strip()]
            elif isinstance(lang, (list, set, tuple)):
                langs = list(lang)
            else:
                langs = ['ch_sim', 'en']
            # 智能转换 tesseract -> easyocr
            langs = [LANG_MAP_TESSERACT_TO_EASYOCR.get(l, l) for l in langs]
        self.reader = easyocr.Reader(langs, gpu=True)
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