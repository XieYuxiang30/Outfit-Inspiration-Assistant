from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class GarmentType(str, Enum):
    TOP = "上衣"
    BOTTOM = "裤子"
    SHOES = "鞋子"
    OUTERWEAR = "外套"
    ACCESSORY = "配饰"


class Season(str, Enum):
    SPRING = "春季"
    SUMMER = "夏季"
    AUTUMN = "秋季"
    WINTER = "冬季"
    ALL = "四季"


class Formality(str, Enum):
    CASUAL = "休闲"
    SMART_CASUAL = "商务休闲"
    FORMAL = "正式"
    SPORT = "运动"


class Garment(BaseModel):
    """单件衣物信息"""
    id: str
    type: GarmentType = Field(description="衣物类型")
    color: str = Field(description="主要颜色")
    material: Optional[str] = Field(default=None, description="材质")
    pattern: Optional[str] = Field(default=None, description="图案")
    season: List[Season] = Field(default_factory=lambda: [Season.ALL], description="适合季节")
    formality: Formality = Field(default=Formality.CASUAL, description="正式程度")
    description: str = Field(description="一句话描述")
    image_path: str = Field(description="衣物图片路径")
    embedding: Optional[List[float]] = Field(default=None, description="CLIP向量")


class OutfitItem(BaseModel):
    """穿搭方案中的单品"""
    garment_id: str
    type: str
    description: str
    color: str


class Outfit(BaseModel):
    """完整穿搭方案"""
    top: Optional[OutfitItem] = None
    bottom: Optional[OutfitItem] = None
    shoes: Optional[OutfitItem] = None
    outerwear: Optional[OutfitItem] = None
    accessories: List[OutfitItem] = Field(default_factory=list)
    reason: str = Field(description="推荐理由")


class WardrobeQuery(BaseModel):
    """用户查询"""
    occasion: str = Field(description="场合")
    style: Optional[str] = Field(default=None, description="风格偏好")
    weather_temp: Optional[float] = Field(default=None, description="温度")
    weather_feels_like: Optional[float] = Field(default=None, description="体感温度")
    weather_desc: Optional[str] = Field(default=None, description="天气描述")
