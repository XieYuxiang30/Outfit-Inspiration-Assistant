import requests
import time
from typing import Optional, Dict
from datetime import datetime
from app.config import OPENWEATHER_API_KEY


class WeatherCache:
    """天气缓存"""
    def __init__(self, ttl: int = 600):
        self.cache: Dict[str, tuple] = {}
        self.ttl = ttl

    def get(self, city: str) -> Optional[Dict]:
        if city in self.cache:
            data, ts = self.cache[city]
            if time.time() - ts < self.ttl:
                return data
            del self.cache[city]
        return None

    def set(self, city: str, data: Dict):
        self.cache[city] = (data, time.time())


class WeatherService:
    """天气服务"""

    def __init__(self):
        self.api_key = OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache = WeatherCache()
        self._default_city = "Beijing"

    def get_current_weather(self, city: str) -> Optional[Dict]:
        """获取当前天气，带缓存和降级"""
        city = city or self._default_city
        cached = self.cache.get(city)
        if cached:
            return cached

        if not self.api_key:
            return self._mock_weather(city)

        try:
            response = requests.get(
                f"{self.base_url}/weather",
                params={"q": city, "appid": self.api_key, "units": "metric", "lang": "zh_cn"},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                weather = {
                    "temp": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "city": data["name"],
                    "wind_speed": data.get("wind", {}).get("speed", 0),
                    "updated_at": datetime.now().isoformat(),
                }
                self.cache.set(city, weather)
                return weather
            elif response.status_code == 404:
                return self._mock_weather(city)
        except Exception as e:
            print(f"获取天气失败: {e}")
        return self._mock_weather(city)

    def get_weather_prompt(self, city: str) -> str:
        """获取天气信息并格式化为Prompt"""
        weather = self.get_current_weather(city)
        if weather:
            return (
                f"当前城市：{weather['city']}，"
                f"温度：{weather['temp']}°C，"
                f"体感温度：{weather['feels_like']}°C，"
                f"天气：{weather['description']}，"
                f"湿度：{weather.get('humidity', '未知')}%"
            )
        return "当前天气信息暂不可用，建议根据常识穿搭"

    def _mock_weather(self, city: str) -> Dict:
        """降级：返回默认天气"""
        return {
            "temp": 22,
            "feels_like": 24,
            "description": "多云",
            "humidity": 50,
            "city": city or self._default_city,
            "wind_speed": 3,
            "updated_at": datetime.now().isoformat(),
            "is_mock": True,
        }
