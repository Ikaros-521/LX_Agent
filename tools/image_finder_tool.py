import os
import cv2
import numpy as np
from typing import Optional, List, Dict, Any, Tuple, Union
from PIL import Image

from common.json_utils import dumps, loads
from tools.ocr_backends.base import BaseOCR
from tools.ocr_tool import OCRFactory


class ImageFinderTool:
    """
    图像查找工具，用于在截图中查找文本或图像的位置
    支持两种查找方式：
    1. 通过文本查找：使用OCR识别截图中的文本，然后返回匹配文本的坐标
    2. 通过图像查找：使用模板匹配在截图中查找指定图像的位置
    """
    
    def __init__(self, ocr_backend: str = 'easyocr', lang: Optional[str] = None):
        """
        初始化图像查找工具
        
        Args:
            ocr_backend: OCR后端，支持'easyocr'和'tesseract'
            lang: 语言，默认为None，使用OCR后端的默认语言
        """
        self.ocr = OCRFactory.create(backend=ocr_backend, lang=lang)
    
    def find_text(self, image_path: str, text: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        在图像中查找指定文本的位置
        
        Args:
            image_path: 图像路径
            text: 要查找的文本
            threshold: 匹配阈值，越高要求越精确
            
        Returns:
            List[Dict[str, Any]]: 匹配结果列表，每个结果包含文本、位置和置信度
        """
        # 使用OCR识别图像中的文本
        ocr_results = self.ocr.recognize(image_path, detailed=True)
        
        # 过滤匹配的文本
        matches = []
        for result in ocr_results:
            # 获取文本
            result_text = result.get('text', '')
            
            # 检查是否匹配
            if text.lower() in result_text.lower():
                # 提取位置信息
                if 'bbox' in result:  # EasyOCR格式
                    # EasyOCR返回的是四个角的坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    bbox = result['bbox']
                    x1 = min(point[0] for point in bbox)
                    y1 = min(point[1] for point in bbox)
                    x2 = max(point[0] for point in bbox)
                    y2 = max(point[1] for point in bbox)
                    
                    matches.append({
                        'text': result_text,
                        'left': int(x1),
                        'top': int(y1),
                        'width': int(x2 - x1),
                        'height': int(y2 - y1),
                        'conf': float(result.get('conf', 0.0)),
                        'center_x': int((x1 + x2) / 2),
                        'center_y': int((y1 + y2) / 2)
                    })
                elif all(k in result for k in ['left', 'top', 'width', 'height']):  # Tesseract格式
                    matches.append({
                        'text': result_text,
                        'left': int(result['left']),
                        'top': int(result['top']),
                        'width': int(result['width']),
                        'height': int(result['height']),
                        'conf': float(result.get('conf', 0.0)),
                        'center_x': int(result['left'] + result['width'] / 2),
                        'center_y': int(result['top'] + result['height'] / 2)
                    })
        
        # 按置信度排序
        matches.sort(key=lambda x: x.get('conf', 0.0), reverse=True)
        
        # 确保结果可以被JSON序列化
        return loads(dumps(matches))
    
    def find_image(self, image_path: str, template_path: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        在图像中查找模板图像的位置（模板匹配）
        
        Args:
            image_path: 要搜索的图像路径
            template_path: 模板图像路径
            threshold: 匹配阈值，越高要求越精确
            
        Returns:
            List[Dict[str, Any]]: 匹配结果列表，每个结果包含位置和置信度
        """
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        # 读取模板
        template = cv2.imread(template_path)
        if template is None:
            raise ValueError(f"无法读取模板图像: {template_path}")
        
        # 获取模板尺寸
        h, w = template.shape[:2]
        
        # 执行模板匹配
        # 使用归一化相关系数匹配方法
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        
        # 查找匹配位置
        locations = np.where(result >= threshold)
        matches = []
        
        # 转换为坐标列表
        for pt in zip(*locations[::-1]):  # 反转以获取 (x, y)
            matches.append({
                'left': int(pt[0]),
                'top': int(pt[1]),
                'width': int(w),
                'height': int(h),
                'conf': float(result[pt[1], pt[0]]),  # 获取该位置的匹配度
                'center_x': int(pt[0] + w / 2),
                'center_y': int(pt[1] + h / 2)
            })
        
        # 非极大值抑制，去除重叠的匹配
        matches = self._non_max_suppression(matches, 0.3)
        
        # 按置信度排序
        matches.sort(key=lambda x: x['conf'], reverse=True)
        
        # 确保结果可以被JSON序列化
        return loads(dumps(matches))
    
    def _non_max_suppression(self, matches: List[Dict[str, Any]], overlap_threshold: float) -> List[Dict[str, Any]]:
        """
        非极大值抑制，去除重叠的匹配
        
        Args:
            matches: 匹配结果列表
            overlap_threshold: 重叠阈值，超过该阈值的重叠区域将被抑制
            
        Returns:
            List[Dict[str, Any]]: 抑制后的匹配结果列表
        """
        if not matches:
            return []
        
        # 按置信度排序
        matches = sorted(matches, key=lambda x: x['conf'], reverse=True)
        
        # 初始化保留的匹配结果
        keep = []
        
        while matches:
            # 取出置信度最高的匹配
            best_match = matches.pop(0)
            keep.append(best_match)
            
            # 计算与其他匹配的重叠度，移除重叠度高的匹配
            i = 0
            while i < len(matches):
                # 计算重叠区域
                x1 = max(best_match['left'], matches[i]['left'])
                y1 = max(best_match['top'], matches[i]['top'])
                x2 = min(best_match['left'] + best_match['width'], matches[i]['left'] + matches[i]['width'])
                y2 = min(best_match['top'] + best_match['height'], matches[i]['top'] + matches[i]['height'])
                
                # 计算重叠面积
                overlap_width = max(0, x2 - x1)
                overlap_height = max(0, y2 - y1)
                overlap_area = overlap_width * overlap_height
                
                # 计算两个矩形的面积
                area1 = best_match['width'] * best_match['height']
                area2 = matches[i]['width'] * matches[i]['height']
                
                # 计算重叠比例
                overlap_ratio = overlap_area / min(area1, area2)
                
                # 如果重叠比例超过阈值，移除该匹配
                if overlap_ratio > overlap_threshold:
                    matches.pop(i)
                else:
                    i += 1
        
        return keep

def get_capabilities():
    return ["image_finder_tool"]

def get_tools():
    return [
        {
            "name": "find_text_pos",
            "description": "在图像中查找指定文本的位置",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "图像路径"},
                    "text": {"type": "string", "description": "要查找的文本"},
                    "threshold": {"type": "number", "description": "匹配阈值，越高要求越精确", "default": 0.7},
                    "ocr_backend": {"type": "string", "description": "OCR后端，可选：tesseract、easyocr", "default": "easyocr"},
                    "lang": {"type": "string", "description": "OCR语言，如'ch_sim'、'en'、'ch_sim+en'，可选"}
                },
                "required": ["image_path", "text"]
            }
        },
        {
            "name": "find_image_pos",
            "description": "在图像中查找模板图像的位置（模板匹配）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "要搜索的图像路径"},
                    "template_path": {"type": "string", "description": "模板图像路径"},
                    "threshold": {"type": "number", "description": "匹配阈值，越高要求越精确", "default": 0.8},
                    "ocr_backend": {"type": "string", "description": "OCR后端，可选：tesseract、easyocr", "default": "easyocr"},
                    "lang": {"type": "string", "description": "OCR语言，如'ch_sim'、'en'、'ch_sim+en'，可选"}
                },
                "required": ["image_path", "template_path"]
            }
        }
    ]

def call_tool(name, arguments):
    if name == "find_text_pos":
        # 文找坐标功能
        text = arguments.get("text")
        image_path = arguments.get("image_path")
        threshold = arguments.get("threshold", 0.7)
        ocr_backend = arguments.get("ocr_backend", "easyocr")
        lang = arguments.get("lang")
        if not text or not image_path:
            return {"status": "error", "error": "缺少必要参数text或image_path"}
        try:
            pos_tool = ImageFinderTool(ocr_backend=ocr_backend, lang=lang)
            result = pos_tool.find_text(image_path, text, threshold)
            return {"status": "success", "result": result}
        except BaseException as e:
            return {"status": "error", "error": str(e)}
    elif name == "find_image_pos":
        # 图找坐标功能
        template_path = arguments.get("template_path")
        image_path = arguments.get("image_path")
        threshold = arguments.get("threshold", 0.7)
        ocr_backend = arguments.get("ocr_backend", "easyocr")
        lang = arguments.get("lang")
        if not template_path or not image_path:
            return {"status": "error", "error": "缺少必要参数template_path或image_path"}
        try:
            pos_tool = ImageFinderTool(ocr_backend=ocr_backend, lang=lang)
            result = pos_tool.find_image(image_path, template_path, threshold)
            return {"status": "success", "result": result}
        except BaseException as e:
            return {"status": "error", "error": str(e)}
    else:
        return {"status": "error", "error": f"Unknown tool: {name}"}