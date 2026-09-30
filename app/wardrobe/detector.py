from ultralytics import YOLO
from typing import List, Tuple
import os
from app.config import MODELS_DIR


class GarmentDetector:
    """使用YOLOv8检测衣物"""

    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        # 衣物相关类别（COCO数据集中的衣物类别）
        self.garment_classes = {
            24: "backpack", 25: "umbrella", 26: "handbag", 27: "tie",
            28: "suitcase", 32: "sports ball", 36: "snowboard", 37: "skateboard",
            39: "tennis racket", 41: "skis", 43: "sports ball",
            0: "person", 1: "bicycle", 2: "car", 3: "motorcycle",
            15: "bench", 56: "chair", 57: "couch", 58: "potted plant",
            60: "dining table", 62: "tv", 63: "laptop", 64: "mouse",
            65: "remote", 66: "keyboard", 67: "cell phone"
        }
        # 简化：检测人，然后从人附近裁剪衣物区域
        # 实际项目中应使用专门训练的衣物检测模型

    def detect(self, image_path: str, conf_threshold: float = 0.3) -> List[Tuple[int, int, int, int]]:
        """检测衣物并返回边界框"""
        results = self.model(image_path, conf=conf_threshold, verbose=False)
        bboxes = []
        
        if len(results) > 0 and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                bboxes.append((x1, y1, x2, y2))
        
        # 如果没检测到，返回默认裁剪区域（将图片分成4个区域）
        if not bboxes:
            import cv2
            img = cv2.imread(image_path)
            h, w = img.shape[:2]
            # 上半部分（上衣）
            bboxes.append((0, 0, w, h // 2))
            # 下半部分（裤子）
            bboxes.append((0, h // 2, w, h))
        
        return bboxes[:4]  # 最多返回4件衣物
