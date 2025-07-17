import sys
import argparse
from tools.ocr_tool import OCRFactory

def main():
    parser = argparse.ArgumentParser(description='OCR工具测试脚本')
    parser.add_argument('--image', required=True, help='图片路径')
    parser.add_argument('--backend', default='tesseract', choices=['tesseract', 'easyocr'], help='OCR后端')
    parser.add_argument('--lang', default='chi_sim+eng', help='OCR语言，如chi_sim、eng、chi_sim+eng')
    args = parser.parse_args()

    print(f'使用后端: {args.backend}, 语言: {args.lang}')
    ocr = OCRFactory.create(args.backend, lang=args.lang)
    text = ocr.recognize(args.image, lang=args.lang)
    print('识别结果:')
    print(text)

if __name__ == '__main__':
    main() 