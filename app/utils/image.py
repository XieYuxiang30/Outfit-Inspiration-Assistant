import cv2
import numpy as np
from PIL import Image
from typing import Tuple, List
import os


def load_image(image_path: str) -> np.ndarray:
    """加载图片为OpenCV格式"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法加载图片: {image_path}")
    return img


def save_crop(image: np.ndarray, bbox: Tuple[int, int, int, int], output_path: str):
    """裁剪图片并保存"""
    x1, y1, x2, y2 = bbox
    h, w = image.shape[:2]
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)
    crop = image[y1:y2, x1:x2]
    if crop.size > 0:
        cv2.imwrite(output_path, crop)


def get_crops(
    image_path: str,
    bboxes: List[Tuple[int, int, int, int]],
    output_dir: str,
    prefix: str = "garment",
) -> List[str]:
    """批量裁剪图片"""
    image = load_image(image_path)
    crop_paths = []
    for i, bbox in enumerate(bboxes):
        output_path = os.path.join(output_dir, f"{prefix}_{i}.jpg")
        save_crop(image, bbox, output_path)
        if os.path.exists(output_path):
            crop_paths.append(output_path)
    return crop_paths


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """PIL图片转OpenCV格式"""
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
    """OpenCV图片转PIL格式"""
    return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
