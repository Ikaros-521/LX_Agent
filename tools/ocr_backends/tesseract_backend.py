from tools.ocr_tool import BaseOCR

class TesseractOCR(BaseOCR):
    def __init__(self, lang=None):
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError("请先安装 pytesseract 和 pillow")
        self.pytesseract = pytesseract
        self.Image = Image
        self.lang = lang or 'chi_sim+eng'
    def recognize(self, image_path: str, lang=None, detailed: bool = False):
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