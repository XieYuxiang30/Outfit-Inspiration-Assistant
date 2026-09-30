import json
import requests
from typing import List
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.utils.schema import WardrobeQuery, Outfit, Garment, OutfitItem


class OutfitGenerator:
    """穿搭方案生成器"""

    def __init__(self):
        self.api_key = LLM_API_KEY
        self.base_url = LLM_BASE_URL
        self.model = LLM_MODEL

    def generate(self, query: WardrobeQuery, garments: List[Garment]) -> List[Outfit]:
        """根据查询和衣物生成穿搭方案"""
        if not self.api_key:
            return self._mock_generate(query, garments)

        garments_text = "\n".join([
            f"- {g.type.value}: {g.color} {g.description} ({g.formality.value})"
            for g in garments[:10]  # 最多取10件
        ])

        prompt = f"""你是一位专业的穿搭顾问，擅长结合潮流趋势和场合需求给出穿搭建议。

当前信息：
- 温度：{query.weather_temp or '未知'}°C，体感：{query.weather_feels_like or '未知'}°C
- 天气：{query.weather_desc or '未知'}
- 场合：{query.occasion}
- 风格偏好：{query.style or '无'}

用户衣橱中的衣物：
{garments_text if garments_text else "（暂无衣物，请推荐通用方案）"}

请以JSON格式输出3套穿搭方案，每套包含：
{{
  "outfits": [
    {{
      "top": {{"type": "上衣类型", "description": "描述", "color": "颜色"}},
      "bottom": {{"type": "裤子类型", "description": "描述", "color": "颜色"}},
      "shoes": {{"type": "鞋子类型", "description": "描述", "color": "颜色"}},
      "outerwear": {{"type": "外套类型", "description": "描述", "color": "颜色"}} or null,
      "accessories": [],
      "reason": "推荐理由"
    }}
  ]
}}

确保JSON格式正确。"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是穿搭顾问，只输出JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # 解析JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            outfits = []
            for item in data.get("outfits", [])[:3]:
                outfit = Outfit(
                    top=OutfitItem(**item["top"]) if item.get("top") else None,
                    bottom=OutfitItem(**item["bottom"]) if item.get("bottom") else None,
                    shoes=OutfitItem(**item["shoes"]) if item.get("shoes") else None,
                    outerwear=OutfitItem(**item["outerwear"]) if item.get("outerwear") else None,
                    accessories=[OutfitItem(**a) for a in item.get("accessories", [])],
                    reason=item.get("reason", ""),
                )
                outfits.append(outfit)
            return outfits
        except Exception as e:
            print(f"生成穿搭方案失败: {e}")
            return self._mock_generate(query, garments)

    def generate_with_trends(
        self,
        query: WardrobeQuery,
        garments: List[Garment],
        trend_context: str = "",
    ) -> List[Outfit]:
        """带潮流上下文的穿搭生成"""
        if not self.api_key:
            return self._mock_generate(query, garments)

        garments_text = "\n".join([
            f"- {g.type.value}: {g.color} {g.description} ({g.formality.value})"
            for g in garments[:10]
        ]) or "（暂无衣物，请推荐通用方案）"

        trend_section = f"\n参考潮流趋势：\n{trend_context}\n" if trend_context else ""

        prompt = f"""你是一位专业的穿搭顾问，擅长结合潮流趋势和场合需求给出穿搭建议。

当前信息：
- 温度：{query.weather_temp or '未知'}°C，体感：{query.weather_feels_like or '未知'}°C
- 天气：{query.weather_desc or '未知'}
- 场合：{query.occasion}
- 风格偏好：{query.style or '无'}
{trend_section}用户衣橱中的衣物：
{garments_text}

请以JSON格式输出3套穿搭方案，每套包含：
{{
  "outfits": [
    {{
      "top": {{"type": "上衣类型", "description": "描述", "color": "颜色"}},
      "bottom": {{"type": "裤子类型", "description": "描述", "color": "颜色"}},
      "shoes": {{"type": "鞋子类型", "description": "描述", "color": "颜色"}},
      "outerwear": {{"type": "外套类型", "description": "描述", "color": "颜色"}} or null,
      "accessories": [],
      "reason": "推荐理由"
    }}
  ]
}}

确保JSON格式正确。"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是穿搭顾问，只输出JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            outfits = []
            for item in data.get("outfits", [])[:3]:
                outfit = Outfit(
                    top=OutfitItem(**item["top"]) if item.get("top") else None,
                    bottom=OutfitItem(**item["bottom"]) if item.get("bottom") else None,
                    shoes=OutfitItem(**item["shoes"]) if item.get("shoes") else None,
                    outerwear=OutfitItem(**item["outerwear"]) if item.get("outerwear") else None,
                    accessories=[OutfitItem(**a) for a in item.get("accessories", [])],
                    reason=item.get("reason", ""),
                )
                outfits.append(outfit)
            return outfits
        except Exception as e:
            print(f"生成穿搭方案失败: {e}")
            return self._mock_generate(query, garments)

    def _mock_generate(self, query: WardrobeQuery, garments: List[Garment]) -> List[Outfit]:
        """Mock生成（无API时使用）"""
        return [
            Outfit(
                top=OutfitItem(garment_id="mock1", type="T恤", description="简约白色T恤", color="白色"),
                bottom=OutfitItem(garment_id="mock2", type="牛仔裤", description="经典直筒牛仔裤", color="蓝色"),
                shoes=OutfitItem(garment_id="mock3", type="运动鞋", description="百搭小白鞋", color="白色"),
                reason=f"适合{query.occasion}的简约休闲搭配，清爽舒适。"
            ),
            Outfit(
                top=OutfitItem(garment_id="mock4", type="卫衣", description="Oversize卫衣", color="黑色"),
                bottom=OutfitItem(garment_id="mock5", type="工装裤", description="宽松工装裤", color="卡其色"),
                shoes=OutfitItem(garment_id="mock6", type="篮球鞋", description="实战篮球鞋", color="黑白"),
                reason="街头风格，适合日常和轻度运动。"
            ),
        ]
