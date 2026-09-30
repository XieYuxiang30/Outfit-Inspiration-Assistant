from app.utils.schema import WardrobeQuery


class PromptTemplate:
    """Prompt模板管理"""

    @staticmethod
    def outfit_recommendation(query: WardrobeQuery, garments: list) -> str:
        """穿搭推荐Prompt"""
        garments_text = "\n".join([
            f"- {g.type.value}: {g.color} {g.description} ({g.formality.value})"
            for g in garments[:10]
        ]) if garments else "暂无衣物数据"

        return f"""你是一位专业的穿搭顾问，擅长结合潮流趋势和场合需求给出穿搭建议。

当前信息：
- 温度：{query.weather_temp or '未知'}°C，体感：{query.weather_feels_like or '未知'}°C
- 天气：{query.weather_desc or '未知'}
- 场合：{query.occasion}
- 风格偏好：{query.style or '无'}

用户衣橱中的衣物：
{garments_text}

请以JSON格式输出3套穿搭方案，每套包含top、bottom、shoes、outerwear（可为null）、accessories数组和reason字段。
确保JSON格式正确，不要输出其他内容。"""

    @staticmethod
    def garment_extraction() -> str:
        """衣物属性提取Prompt"""
        return """请分析这件衣物图片，提取以下信息并以JSON格式返回：
{
  "type": "上衣/裤子/鞋子/外套/配饰",
  "color": "主要颜色",
  "material": "材质（如棉、涤纶等）",
  "pattern": "图案（如纯色、条纹、印花等）",
  "season": ["适合季节"],
  "formality": "正式程度（休闲/商务休闲/正式/运动）",
  "description": "一句话描述"
}
只返回JSON。"""
