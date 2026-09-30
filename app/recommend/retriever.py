from typing import List
from app.wardrobe.storage import WardrobeStorage
from app.utils.schema import Garment, WardrobeQuery


class WardrobeRetriever:
    """衣橱向量检索器"""

    def __init__(self):
        self.storage = WardrobeStorage()

    def retrieve(self, query: WardrobeQuery, top_k: int = 10) -> List[Garment]:
        """根据查询检索相关衣物"""
        # 构建检索文本
        search_text = f"{query.occasion} {query.style or ''}"

        # 构建过滤条件
        filters = {}
        if query.weather_temp is not None:
            if query.weather_temp < 10:
                filters["season"] = {"$in": ["冬季", "四季"]}
            elif query.weather_temp < 20:
                filters["season"] = {"$in": ["春季", "秋季", "四季"]}
            else:
                filters["season"] = {"$in": ["夏季", "四季"]}

        return self.storage.search(search_text, top_k=top_k, filters=filters if filters else None)

    def get_weather_appropriate(self, temp: float) -> List[Garment]:
        """获取适合当前温度的衣物"""
        return self.storage.get_all()  # 简化：实际应使用filter查询
