# 🚀 部署指南

本文档提供多种部署方式，从最简单到生产级。

---

## 方式一：本地运行（推荐用于开发）

```powershell
# 1. 克隆仓库
git clone https://github.com/XieYuxiang30/Outfit-Inspiration-Assistant.git
cd Outfit-Inspiration-Assistant

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy .env.example .env
# 编辑 .env 填入 API Key

# 4. 启动
streamlit run app/main.py
```

访问 `http://localhost:8501`

---

## 方式二：Streamlit Community Cloud（免费托管）

1. Fork 本仓库到你的 GitHub 账号
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 点击 "New app"，选择你的仓库
4. 设置主文件路径：`app/main.py`
5. 在 "Advanced settings" 中添加 Secrets（对应 `.env` 内容）
6. 点击部署，等待几分钟即可访问

**优点**：
- 完全免费
- 自动 HTTPS
- 支持自定义域名
- 自动更新（Push 到 GitHub 自动重新部署）

---

## 方式三：Railway / Render（生产级）

### Railway

1. 访问 [railway.app](https://railway.app)
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择本仓库
4. 添加环境变量（在 Settings → Variables）
5.  Railway 会自动检测 `requirements.txt` 并部署

### Render

1. 访问 [render.com](https://render.com)
2. 点击 "New" → "Web Service"
3. 连接 GitHub 仓库
4. 配置：
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app/main.py --server.port $PORT`
5. 添加环境变量
6. 部署

---

## 方式四：Docker 部署

### 1. 构建镜像

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. 构建和运行

```powershell
# 构建
docker build -t outfit-assistant .

# 运行
docker run -d -p 8501:8501 \
  -e MULTIMODAL_API_KEY=your_key \
  -e LLM_API_KEY=your_key \
  -e OPENWEATHER_API_KEY=your_key \
  outfit-assistant
```

---

## 方式五：本地 Ollama 离线部署

适合隐私敏感场景，完全离线运行。

### 1. 安装 Ollama

```powershell
# Windows: 下载安装包
# https://ollama.com/download/windows

# 验证安装
ollama --version
```

### 2. 拉取模型

```powershell
# 推荐模型（平衡速度和效果）
ollama pull qwen2.5:4b

# 或 Gemma 3
ollama pull gemma3:4b
```

### 3. 启动 Ollama 服务

```powershell
ollama serve
```

### 4. 配置应用

在 `.env` 中注释掉云端 LLM 配置，或在侧边栏勾选 "使用 Ollama 本地模型"。

### 5. 启动应用

```powershell
streamlit run app/main.py
```

**数据流**：所有推理在本地完成，衣物照片不会离开你的电脑。

---

## 🔒 安全注意事项

### API Key 管理

- **不要**将 `.env` 文件提交到 Git
- 使用 GitHub Secrets 管理生产环境密钥
- 定期轮换 API Key
- 为不同环境使用不同的 Key

### 数据隐私

- 衣物照片存储在本地 `data/uploads/`
- 向量数据库存储在本地 `data/chroma_db/`
- 云端部署时，确保 `data/` 目录有持久化存储
- 敏感数据建议加密存储

### 输入验证

生产环境需加强：
- 图片文件类型验证
- 文件大小限制
- API 调用频率限制
- SQL/NoSQL 注入防护

---

## 📊 性能优化建议

### 模型优化

- YOLOv8n → YOLOv8s 提升检测准确率（牺牲速度）
- CLIP ViT-B/32 → ViT-L/14 提升检索精度
- LLM 使用流式响应，减少首字延迟

### 缓存策略

- 天气数据缓存 10 分钟
- 潮流知识库本地持久化
- 向量检索结果缓存

### 并发处理

- Streamlit 默认单用户，生产环境建议用 `streamlit>=1.28` + `--server.maxUploadSize`
- 多用户场景考虑 FastAPI + Vue/React 重构

---

## 🐛 常见问题

### 1. YOLO 模型下载慢

```powershell
# 手动下载到 data/models/
yolov8n.pt
# https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### 2. ChromaDB 报错

```powershell
# 删除旧数据库重新初始化
rm -rf data/chroma_db
streamlit run app/main.py
```

### 3. 内存不足

- 减少 `top_k` 参数（如从 10 改为 5）
- 使用 `sentence-transformers` 的小模型
- 关闭 Ollama 时减少内存占用

---

## 📦 打包为 Windows exe

如需打包为桌面应用，可使用 PyInstaller：

```powershell
pip install pyinstaller

pyinstaller --onefile \
  --add-data "app;app" \
  --add-data ".env.example;." \
  run.py
```

---

## 🔗 相关链接

- [Streamlit 文档](https://docs.streamlit.io)
- [Ultralytics YOLOv8](https://docs.ultralytics.com)
- [ChromaDB](https://docs.trychroma.com)
- [Sentence Transformers](https://www.sbert.net)
- [Ollama](https://ollama.com)
- [阿里云 DashScope](https://dashscope.aliyun.com)
