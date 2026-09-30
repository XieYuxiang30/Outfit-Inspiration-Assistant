from typing import Dict
from app.utils.schema import WardrobeQuery
from app.recommend.retriever import WardrobeRetriever
from app.recommend.generator import OutfitGenerator
from app.rag.retriever import TrendRetriever
from app.recommend.evaluator import OutfitEvaluator
from app.recommend.weather import WeatherService
from app.styles.hiphop import HipHopStyleEngine
from app.styles.basketball import BasketballStyleEngine
from app.local.ollama import get_ollama_client


class RecommendationPipeline:
    """推荐流水线：检索→生成→评估"""

    def __init__(self):
        self.weather_service = WeatherService()
        self.wardrobe_retriever = WardrobeRetriever()
        self.trend_retriever = TrendRetriever()
        self.generator = OutfitGenerator()
        self.evaluator = OutfitEvaluator()
        self.ollama = get_ollama_client()

    def run(self, query: WardrobeQuery, use_local: bool = False) -> Dict:
        """执行完整推荐流程"""
        # 1. 获取天气
        weather = self.weather_service.get_current_weather(query.city or "Beijing")
        query.weather_temp = weather.get("temp") if weather else None
        query.weather_feels_like = weather.get("feels_like") if weather else None
        query.weather_desc = weather.get("description") if weather else None

        # 2. 检索衣橱衣物
        garments = self.wardrobe_retriever.retrieve(query, top_k=10)

        # 3. 差异化处理
        extra_prompt = ""
        trends = []
        if query.occasion == "打球":
            garments = BasketballStyleEngine.rank_for_basketball(garments)
            extra_prompt = BasketballStyleEngine.build_basketball_prompt(query, garments)
            tips = BasketballStyleEngine.get_basketball_tips()
        elif HipHopStyleEngine.is_hiphop_occasion(query.occasion) or (query.style and "hiphop" in query.style.lower()):
            garments = HipHopStyleEngine.rank_garments(garments)
            extra_prompt = HipHopStyleEngine.build_prompt_suffix(query)
            tips = []
        else:
            tips = []

        # 4. RAG检索潮流信息
        trends = self.trend_retriever.retrieve(query, top_k=3)
        trend_context = "\n".join([f"- {t}" for t in trends]) if trends else ""

        # 5. 生成穿搭方案
        if use_local and self.ollama.is_available():
            outfits = self.ollama.generate_outfits(query, garments)
        else:
            combined_prompt = f"{extra_prompt}\n参考潮流趋势：\n{trend_context}\n" if trend_context else extra_prompt
            outfits = self.generator.generate_with_trends(query, garments, combined_prompt)

        # 6. 评估方案
        evaluations = self.evaluator.evaluate_outfits(outfits, weather, query.occasion)

        return {
            "outfits": outfits,
            "evaluations": evaluations,
            "weather": weather,
            "trends": trends,
            "garments_used": [g.id for g in garments],
            "tips": tips,
        }
