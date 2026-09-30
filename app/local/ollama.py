"""
Ollama 本地部署支持
支持使用本地小模型（如 Qwen2.5:4B、Gemma3:4B）运行，保护数据隐私
"""

from typing import List, Optional
import requests
from app.utils.schema import WardrobeQuery, Outfit, OutfitItem, Garment


class OllamaClient:
    """Ollama 本地模型客户端"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.default_model = "qwen2.5:4b"

    def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """获取已安装的模型列表"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def generate_outfits(
        self,
        query: WardrobeQuery,
        garments: List[Garment],
        model: Optional[str] = None,
    ) -> List[Outfit]:
        """使用本地模型生成穿搭方案"""
        if not self.is_available():
            return []

        model = model or self.default_model
        garments_text = "\n".join([
            f"- {g.type.value}: {g.color} {g.description}"
            for g in garments[:10]
        ]) or "暂无衣物"

        prompt = f"""你是一位专业的穿搭顾问。
温度：{query.weather_temp or '未知'}°C，天气：{query.weather_desc or '未知'}
场合：{query.occasion}
风格：{query.style or '无'}

衣橱衣物：
{garments_text}

请输出3套穿搭方案，JSON格式：
{{
  "outfits": [
    {{
      "top": {{"type": "上衣", "description": "描述", "color": "颜色"}},
      "bottom": {{"type": "裤子", "description": "描述", "color": "颜色"}},
      "shoes": {{"type": "鞋子", "description": "描述", "color": "颜色"}},
      "outerwear": null,
      "accessories": [],
      "reason": "理由"
    }}
  ]
}}"""

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 500},
                },
                timeout=120,
            )
            data = resp.json()
            content = data.get("response", "")

            # 简单解析 JSON
            import json
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                result = json.loads(match.group())
                outfits = []
                for item in result.get("outfits", [])[:3]:
                    outfits.append(Outfit(
                        top=OutfitItem(**item["top"]) if item.get("top") else None,
                        bottom=OutfitItem(**item["bottom"]) if item.get("bottom") else None,
                        shoes=OutfitItem(**item["shoes"]) if item.get("shoes") else None,
                        outerwear=OutfitItem(**item["outerwear"]) if item.get("outerwear") else None,
                        accessories=[OutfitItem(**a) for a in item.get("accessories", [])],
                        reason=item.get("reason", ""),
                    ))
                return outfits
        except Exception:
            pass
        return []

    def generate_response(self, prompt: str, model: Optional[str] = None) -> str:
        """通用对话生成"""
        if not self.is_available():
            return ""
        model = model or self.default_model
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            return resp.json().get("response", "")
        except Exception:
            return ""


def get_ollama_client() -> OllamaClient:
    """获取 Ollama 客户端单例"""
    if not hasattr(get_ollama_client, "_instance"):
        get_ollama_client._instance = OllamaClient()
    return get_ollama_client._instance
