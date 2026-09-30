"""
篮球场景专项优化模块
"""

from typing import List
from app.utils.schema import Garment, GarmentType


class BasketballStyleEngine:
    """篮球场景风格引擎"""

    # 篮球场景关键词
    KEYWORDS = [
        "篮球鞋", "实战", "高帮", "低帮", "球鞋", "sneaker", "basketball",
        "速干", "压缩", "护膝", "运动袜", "运动短裤", "篮球服"
    ]

    # 知名篮球鞋型号关键词
    SNEAKER_MODELS = [
        "gt cut", "harden", "lebron", "kobe", "jordan", "kyrie",
        "curry", "dame", "luka", "trim", "air jordan", "nike",
        "adidas", "under armour", "puma", "anta", "li-ning"
    ]

    @classmethod
    def is_basketball_gear(cls, garment: Garment) -> bool:
        """判断是否为篮球相关装备"""
        text = f"{garment.type.value} {garment.description} {garment.pattern or ''}".lower()
        return any(kw in text for kw in cls.KEYWORDS)

    @classmethod
    def is_basketball_shoe(cls, garment: Garment) -> bool:
        """判断是否为篮球鞋"""
        if garment.type != GarmentType.SHOES:
            return False
        text = garment.description.lower()
        return any(m in text for m in cls.SNEAKER_MODELS) or "篮球" in text

    @classmethod
    def score_for_basketball(cls, garment: Garment) -> int:
        """计算衣物在篮球场景的匹配分数"""
        score = 0
        text = f"{garment.type.value} {garment.description}".lower()

        # 类型加分
        if garment.type == GarmentType.SHOES:
            score += 5
            if cls.is_basketball_shoe(garment):
                score += 10
        elif garment.type == GarmentType.TOP:
            score += 3
            if any(k in text for k in ["速干", "短袖", "背心"]):
                score += 5
        elif garment.type == GarmentType.BOTTOM:
            score += 2
            if any(k in text for k in ["短裤", "压缩裤"]):
                score += 5
        elif garment.type == GarmentType.ACCESSORY:
            score += 1
            if any(k in text for k in ["护膝", "运动袜", "发带"]):
                score += 3

        return score

    @classmethod
    def rank_for_basketball(cls, garments: List[Garment]) -> List[Garment]:
        """按篮球场景对衣物排序"""
        return sorted(garments, key=cls.score_for_basketball, reverse=True)

    @classmethod
    def build_basketball_prompt(cls, query, garments: List[Garment]) -> str:
        """构建篮球场景专用 Prompt"""
        ranked = cls.rank_for_basketball(garments)
        garments_text = "\n".join([
            f"- {g.type.value}: {g.color} {g.description} (篮球匹配度: {cls.score_for_basketball(g)})"
            for g in ranked[:10]
        ]) or "暂无篮球相关衣物"

        return f"""你是一位专业的篮球穿搭顾问。

当前场景：篮球场实战
温度：{query.weather_temp or '未知'}°C
天气：{query.weather_desc or '未知'}

用户衣橱中的衣物（已按篮球匹配度排序）：
{garments_text}

请以JSON格式输出3套篮球场穿搭方案，优先选择：
- 速干/透气的上衣
- 运动短裤/压缩裤
- 专业篮球鞋
- 必要的运动配件（护膝、运动袜等）

输出格式：
{{
  "outfits": [
    {{
      "top": {{"type": "上衣", "description": "描述", "color": "颜色"}},
      "bottom": {{"type": "裤子", "description": "描述", "color": "颜色"}},
      "shoes": {{"type": "鞋子", "description": "描述", "color": "颜色"}},
      "accessories": [{{"type": "配件", "description": "描述", "color": "颜色"}}],
      "reason": "推荐理由"
    }}
  ]
}}"""

    @classmethod
    def get_basketball_tips(cls) -> List[str]:
        """获取篮球穿搭小贴士"""
        return [
            "🏀 选择速干面料，保持干爽舒适",
            "👟 优先选择专业篮球鞋，提供足够的脚踝支撑",
            "🧦 搭配运动袜，防止磨脚",
            "🩱 压缩裤可以有效减少肌肉疲劳",
            "🧢 棒球帽可以遮挡阳光，增加潮流感",
            "💪 护膝等防护装备不可少",
        ]
