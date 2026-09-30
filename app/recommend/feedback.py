import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from app.config import DATA_DIR
from app.utils.schema import Outfit


class FeedbackStore:
    """用户反馈存储"""

    def __init__(self):
        self.feedback_path = os.path.join(DATA_DIR, "feedback.json")
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.feedback_path):
            with open(self.feedback_path, "w", encoding="utf-8") as f:
                json.dump({"feedback": []}, f, ensure_ascii=False)

    def add_feedback(self, outfit: Outfit, rating: int, comment: str = "", occasion: str = "", style: str = ""):
        """添加反馈"""
        data = self._load()
        data["feedback"].append({
            "outfit": outfit.model_dump() if hasattr(outfit, "model_dump") else outfit.dict(),
            "rating": rating,
            "comment": comment,
            "occasion": occasion,
            "style": style,
            "created_at": datetime.now().isoformat(),
        })
        self._save(data)

    def get_recent_feedback(self, limit: int = 20) -> List[Dict]:
        """获取最近反馈"""
        data = self._load()
        return data["feedback"][-limit:]

    def get_statistics(self) -> Dict:
        """获取反馈统计"""
        data = self._load()
        feedbacks = data["feedback"]
        if not feedbacks:
            return {"count": 0, "avg_rating": 0}
        
        ratings = [f["rating"] for f in feedbacks]
        return {
            "count": len(feedbacks),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
            "positive": sum(1 for r in ratings if r >= 4),
            "negative": sum(1 for r in ratings if r <= 2),
        }

    def _load(self) -> Dict:
        with open(self.feedback_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict):
        with open(self.feedback_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)