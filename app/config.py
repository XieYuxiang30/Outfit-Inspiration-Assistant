import os
from dotenv import load_dotenv

load_dotenv()

# 应用配置
APP_TITLE = os.getenv("APP_TITLE", "穿搭灵感助手")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Beijing")

# 多模态模型配置
MULTIMODAL_API_KEY = os.getenv("MULTIMODAL_API_KEY", "")
MULTIMODAL_BASE_URL = os.getenv("MULTIMODAL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MULTIMODAL_MODEL = os.getenv("MULTIMODAL_MODEL", "qwen-vl-max")

# LLM配置
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-turbo")

# 天气API
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
MODELS_DIR = os.path.join(DATA_DIR, "models")

# 创建必要目录
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# YOLO配置
YOLO_MODEL = "yolov8n.pt"
