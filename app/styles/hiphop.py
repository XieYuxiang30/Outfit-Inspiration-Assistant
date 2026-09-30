"""
说唱/Hip-Hop 风格专属模块
"""

from app.utils.schema import WardrobeQuery, Garment
from typing import List


class HipHopStyleEngine:
    """Hip-Hop 风格引擎"""

    # Hip-Hop 核心风格规则
    KEYWORDS = [
        "oversize", "baggy", "宽松", "街头", "hiphop", "hip-hop",
        "涂鸦", "graffiti", "棒球服", "篮球鞋", "金链子", "腰包",
        "卫衣", "工装裤", "牛仔", "logo", "潮牌", "高街"
    ]

    # 推荐优先级权重
    WEIGHTS = {
        "oversize": 3,
        "baggy": 3,
        "宽松": 3,
        "街头": 2,
        "涂鸦": 2,
        "棒球服": 2,
        "篮球鞋": 2,
        "腰包": 1,
        "卫衣": 2,
        "工装裤": 2,
    }

    @classmethod
    def build_prompt_suffix(cls, query: WardrobeQuery) -> str:
        """生成 Hip-Hop 风格专用 Prompt 后缀"""
        return """
[Hip-Hop Style Rules]
- 优先推荐 Oversize / Baggy 版型
- 配色优先：黑/白/灰 + 高饱和亮色（红/蓝/绿）
- 必选元素：卫衣/棒球服/工装裤/篮球鞋
- 配饰：腰包、棒球帽、金链子
- 避免：修身、商务、正装
- 语气：街头、自信、潮流感
"""

    @classmethod
    def score_garment(cls, garment: Garment) -> int:
        """为衣物计算 Hip-Hop 匹配分数"""
        text = f"{garment.type.value} {garment.color} {garment.description} {garment.pattern or ''}".lower()
        score = 0
        for kw, w in cls.WEIGHTS.items():
            if kw in text:
                score += w
        return score

    @classmethod
    def rank_garments(cls, garments: List[Garment]) -> List[Garment]:
        """按 Hip-Hop 风格对衣物排序"""
        return sorted(garments, key=cls.score_garment, reverse=True)

    @classmethod
    def is_hiphop_occasion(cls, occasion: str) -> bool:
        """判断是否为 Hip-Hop 风格场合"""
        hiphop_occasions = ["聚会", "录音棚", "打球", "逛街", "日常"]
        return occasion in hiphop_occasions

    @classmethod
    def get_default_style(cls, occasion: str) -> str:
        """获取场合默认风格"""
        if cls.is_hiphop_occasion(occasion):
            return "Hip-Hop / Oversize / 街头"
        return "简约休闲"
