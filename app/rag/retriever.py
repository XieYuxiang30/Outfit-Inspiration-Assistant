from typing import List, Optional
from app.rag.knowledge_base import TrendKnowledgeBase
from app.utils.schema import WardrobeQuery


class TrendRetriever:
    """潮流趋势检索器"""

    def __init__(self):
        self.kb = TrendKnowledgeBase()
        # 首次使用加载示例数据
        try:
            self.kb.load_sample_trends()
        except Exception:
            pass

    def retrieve(self, query: WardrobeQuery, top_k: int = 3) -> List[str]:
        """检索相关潮流信息"""
        search_text = f"{query.occasion} {query.style or ''} 穿搭 潮流"
        results = self.kb.search(search_text, top_k=top_k)
        return [r["content"] for r in results]

    def get_style_guide(self, style: str) -> Optional[str]:
        """获取特定风格的指南"""
        results = self.kb.search(f"{style} 风格 穿搭指南", top_k=1)
        if results:
            return results[0]["content"]
        return None