import os
import json
import hashlib
from typing import List, Optional
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer
from app.config import DATA_DIR
from app.utils.schema import Garment


class TrendKnowledgeBase:
    """潮流趋势知识库"""

    def __init__(self):
        self.db_path = os.path.join(DATA_DIR, "trends_db")
        os.makedirs(self.db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="fashion_trends",
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_model = SentenceTransformer("clip-ViT-B-32")

    def add_trend(self, content: str, source: str, metadata: Optional[Dict] = None):
        """添加潮流内容"""
        doc_id = hashlib.md5(f"{source}_{content[:50]}".encode()).hexdigest()
        embedding = self.embedding_model.encode(content).tolist()
        
        meta = {
            "source": source,
            "created_at": datetime.now().isoformat(),
            "type": metadata.get("type", "article") if metadata else "article",
        }
        if metadata:
            meta.update(metadata)
        
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[meta],
            ids=[doc_id],
        )

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关潮流内容"""
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        
        trends = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                trends.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": results["distances"][0][i] if "distances" in results else 0,
                })
        return trends

    def load_sample_trends(self):
        """加载示例潮流数据"""
        sample_trends = [
            {
                "content": "2024年秋冬流行 Oversize 版型，搭配宽松工装裤和厚底鞋，街头风格强势回归。",
                "source": "小红书",
                "type": "trend",
            },
            {
                "content": "Hip-Hop 风格核心元素：棒球服、金链子、运动鞋、腰包，配色以黑白灰为主。",
                "source": "Instagram",
                "type": "style_guide",
            },
            {
                "content": "篮球场穿搭推荐：速干T恤+ compression shorts + 高帮篮球鞋，功能性优先。",
                "source": "Nike Blog",
                "type": "sport",
            },
            {
                "content": "面试穿搭建议：深色西装+纯色衬衫+皮鞋，颜色以藏蓝、灰色为主，避免印花。",
                "source": "职场指南",
                "type": "formal",
            },
            {
                "content": "约会穿搭：浅色系毛衣+休闲裤+小白鞋，营造温柔干净的形象。",
                "source": "时尚博主",
                "type": "casual",
            },
        ]
        
        for trend in sample_trends:
            self.add_trend(trend["content"], trend["source"], {"type": trend["type"]})
