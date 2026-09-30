import json
import requests
from typing import List, Dict, Optional
from app.config import MULTIMODAL_API_KEY, MULTIMODAL_BASE_URL, MULTIMODAL_MODEL
from app.utils.schema import Outfit


class OutfitEvaluator:
    """穿搭质量评估器（VLM Judge）"""

    def __init__(self):
        self.api_key = MULTIMODAL_API_KEY
        self.base_url = MULTIMODAL_BASE_URL
        self.model = MULTIMODAL_MODEL

    def evaluate(self, outfit: Outfit, weather: Optional[Dict] = None, occasion: str = "") -> Dict:
        """评估单套穿搭方案"""
        if not self.api_key:
            return self._mock_evaluate(outfit)

        prompt = f"""你是一位专业的穿搭评估师。请从以下三个维度评分（1-10分）：

1. 设计感（Design Score）：配色、层次、潮流度
2. 合身度（Fitness Score）：版型是否适合场景
3. 整体协调性（Coherence Score）：单品之间是否协调

场景：{occasion}
天气：{weather.get('temp', '未知')}°C，{weather.get('description', '未知') if weather else '未知'}

穿搭方案：
- 上衣：{outfit.top.type if outfit.top else '无'} {outfit.top.color if outfit.top else ''}
- 裤子：{outfit.bottom.type if outfit.bottom else '无'} {outfit.bottom.color if outfit.bottom else ''}
- 鞋子：{outfit.shoes.type if outfit.shoes else '无'} {outfit.shoes.color if outfit.shoes else ''}
- 外套：{outfit.outerwear.type if outfit.outerwear else '无'}
- 配饰：{[a.type for a in outfit.accessories] if outfit.accessories else '无'}

推荐理由：{outfit.reason}

请以JSON格式返回：
{{
  "design_score": 8,
  "fitness_score": 8,
  "coherence_score": 8,
  "total_score": 8,
  "suggestions": "改进建议"
}}"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是穿搭评估师，只输出JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 300,
                },
                timeout=30,
            )
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except Exception as e:
            print(f"评估失败: {e}")
            return self._mock_evaluate(outfit)

    def _mock_evaluate(self, outfit: Outfit) -> Dict:
        """Mock评估"""
        return {
            "design_score": 7,
            "fitness_score": 8,
            "coherence_score": 7,
            "total_score": 7,
            "suggestions": "整体不错，可以尝试加入配饰提升层次感。",
        }

    def evaluate_outfits(self, outfits: List[Outfit], weather: Optional[Dict] = None, occasion: str = "") -> List[Dict]:
        """批量评估"""
        return [self.evaluate(o, weather, occasion) for o in outfits]
