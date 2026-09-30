"""
以图搜图：CLIP 多模态相似检索
"""

from typing import List, Optional
from PIL import Image
from app.wardrobe.storage import WardrobeStorage
from app.utils.schema import Garment
import os


class ImageSearchEngine:
    """以图搜图引擎"""

    def __init__(self):
        self.storage = WardrobeStorage()
        # CLIP 模型用于图片向量化
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("clip-ViT-B-32")
        except Exception:
            self.model = None

    def search_by_image(self, query_image_path: str, top_k: int = 5) -> List[Garment]:
        """根据图片搜索相似衣物"""
        if not self.model:
            return []

        # 生成查询图片的向量
        query_emb = self._encode_image(query_image_path)
        if query_emb is None:
            return []

        # 在 ChromaDB 中搜索相似向量
        try:
            results = self.storage.collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
            )
        except Exception:
            return []

        garments = []
        if results.get("ids") and results["ids"][0]:
            for i, gid in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i]
                garments.append(Garment(
                    id=meta.get("garment_id", gid),
                    type=meta.get("type", "上衣"),
                    color=meta.get("color", "未知"),
                    formality=meta.get("formality", "休闲"),
                    image_path=meta.get("image_path", ""),
                    description=results["documents"][0][i] if results.get("documents") else "",
                ))
        return garments

    def _encode_image(self, image_path: str) -> Optional[List[float]]:
        """将图片编码为 CLIP 向量"""
        if not self.model or not os.path.exists(image_path):
            return None
        try:
            img = Image.open(image_path).convert("RGB")
            emb = self.model.encode(img)
            return emb.tolist()
        except Exception:
            return None

    def add_image_garment(self, image_path: str, garment: Garment):
        """添加衣物并生成图片向量"""
        if not self.model:
            self.storage.add_garment(garment)
            return

        emb = self._encode_image(image_path)
        if emb:
            garment.embedding = emb
        self.storage.add_garment(garment)
