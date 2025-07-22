from tools.ocr_tool import BaseOCR

LANG_MAP_EASYOCR_TO_TESSERACT = {
    'ch_sim': 'chi_sim',
    'ch_tra': 'chi_tra',
    'en': 'eng',
    'ja': 'jpn',
    'ko': 'kor',
    # 可扩展
}

class TesseractOCR(BaseOCR):
    def __init__(self, lang=None):
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError("请先安装 pytesseract 和 pillow")
        self.pytesseract = pytesseract
        self.Image = Image
        self.lang = self._convert_lang(lang or 'chi_sim')
    def _convert_lang(self, lang):
        if not lang:
            return 'chi_sim'
        if isinstance(lang, str):
            if '+' in lang:
                langs = [l.strip() for l in lang.split('+')]
            elif ',' in lang:
                langs = [l.strip() for l in lang.split(',')]
            else:
                langs = [lang.strip()]
        elif isinstance(lang, (list, set, tuple)):
            langs = list(lang)
        else:
            langs = ['chi_sim']
        # 智能转换 easyocr -> tesseract
        langs = [LANG_MAP_EASYOCR_TO_TESSERACT.get(l, l) for l in langs]
        return '+'.join(langs)
    def recognize(self, image_path: str, lang=None, detailed: bool = False):
        img = self.Image.open(image_path)
        use_lang = self._convert_lang(lang) if lang else self.lang
        if not detailed:
            return self.pytesseract.image_to_string(img, lang=use_lang)
        else:
            data = self.pytesseract.image_to_data(img, lang=use_lang, output_type=self.pytesseract.Output.DICT)
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