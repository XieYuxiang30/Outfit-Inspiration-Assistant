import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import os
from app.config import CHROMA_DIR
from app.utils.schema import Garment


class WardrobeStorage:
    """使用ChromaDB存储衣物信息"""

    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name="wardrobe",
            metadata={"hnsw:space": "cosine"},
        )
        # 使用CLIP或Sentence-BERT作为embedding模型
        self.embedding_model = SentenceTransformer("clip-ViT-B-32")

    def add_garment(self, garment: Garment):
        """添加衣物到向量数据库"""
        # 生成文本描述用于embedding
        text = f"{garment.type.value} {garment.color} {garment.description}"
        if garment.material:
            text += f" {garment.material}"
        if garment.pattern:
            text += f" {garment.pattern}"
        
        embedding = self.embedding_model.encode(text).tolist()
        garment.embedding = embedding

        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[{
                "garment_id": garment.id,
                "type": garment.type.value,
                "color": garment.color,
                "formality": garment.formality.value,
                "season": ",".join([s.value for s in garment.season]),
                "image_path": garment.image_path,
            }],
            ids=[garment.id],
        )

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[Garment]:
        """向量检索相似衣物"""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters if filters else None,
        )
        
        garments = []
        if results["ids"] and results["ids"][0]:
            for i, garment_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                garments.append(Garment(
                    id=metadata["garment_id"],
                    type=metadata["type"],
                    color=metadata["color"],
                    formality=metadata["formality"],
                    image_path=metadata["image_path"],
                    description=results["documents"][0][i],
                ))
        return garments

    def get_all(self) -> List[Garment]:
        """获取所有衣物"""
        results = self.collection.get()
        garments = []
        if results["ids"]:
            for i, garment_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                garments.append(Garment(
                    id=metadata["garment_id"],
                    type=metadata["type"],
                    color=metadata["color"],
                    formality=metadata["formality"],
                    image_path=metadata["image_path"],
                    description=results["documents"][i],
                ))
        return garments

    def delete(self, garment_id: str):
        """删除衣物"""
        self.collection.delete(ids=[garment_id])
