import base64
import json
import requests
from typing import Dict, Optional
from app.config import MULTIMODAL_API_KEY, MULTIMODAL_BASE_URL, MULTIMODAL_MODEL
from app.utils.schema import Garment, GarmentType, Season, Formality


class GarmentExtractor:
    """使用多模态模型提取衣物结构化属性"""

    def __init__(self):
        self.api_key = MULTIMODAL_API_KEY
        self.base_url = MULTIMODAL_BASE_URL
        self.model = MULTIMODAL_MODEL

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def extract(self, image_path: str) -> Garment:
        """从图片提取衣物属性"""
        if not self.api_key:
            # 无API密钥时返回默认属性
            return self._default_garment(image_path)

        base64_image = self._encode_image(image_path)
        
        prompt = """请分析这件衣物图片，提取以下信息并以JSON格式返回：
{
  "type": "上衣/裤子/鞋子/外套/配饰",
  "color": "主要颜色",
  "material": "材质（如棉、涤纶等）",
  "pattern": "图案（如纯色、条纹、印花等）",
  "season": ["适合季节"],
  "formality": "正式程度（休闲/商务休闲/正式/运动）",
  "description": "一句话描述"
}

只返回JSON，不要其他内容。"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                    "max_tokens": 500,
                },
                timeout=30,
            )
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            # 提取JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            return self._parse_to_garment(image_path, data)
        except Exception as e:
            print(f"属性提取失败: {e}")
            return self._default_garment(image_path)

    def _parse_to_garment(self, image_path: str, data: Dict) -> Garment:
        """将提取的数据转换为Garment对象"""
        type_map = {
            "上衣": GarmentType.TOP, "裤子": GarmentType.BOTTOM,
            "鞋子": GarmentType.SHOES, "外套": GarmentType.OUTERWEAR,
            "配饰": GarmentType.ACCESSORY,
        }
        season_map = {
            "春季": Season.SPRING, "夏季": Season.SUMMER,
            "秋季": Season.AUTUMN, "冬季": Season.WINTER,
        }
        formality_map = {
            "休闲": Formality.CASUAL, "商务休闲": Formality.SMART_CASUAL,
            "正式": Formality.FORMAL, "运动": Formality.SPORT,
        }
        
        seasons = []
        for s in data.get("season", ["四季"]):
            seasons.append(season_map.get(s, Season.ALL))
        
        return Garment(
            id=os.path.basename(image_path).split(".")[0],
            type=type_map.get(data.get("type", "上衣"), GarmentType.TOP),
            color=data.get("color", "未知"),
            material=data.get("material"),
            pattern=data.get("pattern"),
            season=seasons if seasons else [Season.ALL],
            formality=formality_map.get(data.get("formality", "休闲"), Formality.CASUAL),
            description=data.get("description", "无描述"),
            image_path=image_path,
        )

    def _default_garment(self, image_path: str) -> Garment:
        """默认属性（无API时使用）"""
        return Garment(
            id=os.path.basename(image_path).split(".")[0],
            type=GarmentType.TOP,
            color="未知",
            description="待识别",
            image_path=image_path,
        )
