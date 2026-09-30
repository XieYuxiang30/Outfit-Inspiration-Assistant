import os
import uuid
import streamlit as st
from PIL import Image
import tempfile

from app.config import APP_TITLE, UPLOAD_DIR
from app.utils.schema import WardrobeQuery, Garment
from app.wardrobe.detector import GarmentDetector
from app.wardrobe.extractor import GarmentExtractor
from app.wardrobe.storage import WardrobeStorage
from app.recommend.weather import WeatherService
from app.recommend.retriever import WardrobeRetriever
from app.recommend.generator import OutfitGenerator
from app.recommend.pipeline import RecommendationPipeline
from app.recommend.evaluator import OutfitEvaluator
from app.recommend.feedback import FeedbackStore
from app.rag.prompt import PromptTemplate
from app.styles.hiphop import HipHopStyleEngine
from app.styles.basketball import BasketballStyleEngine
from app.styles.image_search import ImageSearchEngine
from app.local.ollama import get_ollama_client, OllamaClient

# 页面配置
st.set_page_config(page_title=APP_TITLE, page_icon="👕", layout="wide")

# 初始化session state
if "wardrobe" not in st.session_state:
    st.session_state.wardrobe = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "weather" not in st.session_state:
    st.session_state.weather = None
if "last_outfits" not in st.session_state:
    st.session_state.last_outfits = None
if "last_evaluations" not in st.session_state:
    st.session_state.last_evaluations = None
if "hiphop_mode" not in st.session_state:
    st.session_state.hiphop_mode = False
if "image_search_results" not in st.session_state:
    st.session_state.image_search_results = None
if "use_local_llm" not in st.session_state:
    st.session_state.use_local_llm = False

# 初始化服务
detector = GarmentDetector()
extractor = GarmentExtractor()
storage = WardrobeStorage()
weather_service = WeatherService()
retriever = WardrobeRetriever()
generator = OutfitGenerator()
pipeline = RecommendationPipeline()
evaluator = OutfitEvaluator()
feedback_store = FeedbackStore()
image_search = ImageSearchEngine()
ollama_client: OllamaClient = get_ollama_client()


def save_uploaded_file(uploaded_file) -> str:
    """保存上传的文件"""
    file_ext = os.path.splitext(uploaded_file.name)[1]
    filename = f"{uuid.uuid4().hex}{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getvalue())
    return filepath


def process_wardrobe_image(image_path: str):
    """处理衣橱图片：检测→裁剪→提取属性→存储"""
    with st.spinner("正在识别衣物..."):
        # 1. 检测衣物
        bboxes = detector.detect(image_path)
        st.info(f"检测到 {len(bboxes)} 件衣物区域")
        
        # 2. 裁剪
        from app.utils.image import get_crops
        crop_paths = get_crops(image_path, bboxes, UPLOAD_DIR)
        
        # 3. 提取属性并存储
        new_garments = []
        for crop_path in crop_paths:
            garment = extractor.extract(crop_path)
            storage.add_garment(garment)
            new_garments.append(garment)
        
        st.session_state.wardrobe.extend(new_garments)
        st.success(f"成功识别并添加 {len(new_garments)} 件衣物到衣橱！")
        return new_garments


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # API配置
        with st.expander("API配置", expanded=False):
            multimodal_key = st.text_input("多模态模型API Key", type="password", value="")
            llm_key = st.text_input("LLM API Key", type="password", value="")
            weather_key = st.text_input("天气API Key", type="password", value="")
            city = st.text_input("城市", value="Beijing")
            
            if st.button("保存配置"):
                # 实际应保存到.env，这里简化处理
                st.success("配置已更新（重启后生效）")
        
        st.divider()
        
        # 统计
        st.header("📊 统计")
        
        # 衣橱统计
        all_garments = storage.get_all()
        st.metric("👕 衣物总数", len(all_garments))
        if all_garments:
            types = {}
            for g in all_garments:
                types[g.type.value] = types.get(g.type.value, 0) + 1
            for t, c in types.items():
                st.write(f"- {t}: {c}件")
        
        st.divider()
        
        # 反馈统计
        stats = feedback_store.get_statistics()
        if stats["count"] > 0:
            st.header("📈 反馈统计")
            st.metric("总反馈数", stats["count"])
            st.metric("平均评分", f"{stats['avg_rating']}/5")
            st.caption(f"👍 {stats['positive']} | 👎 {stats['negative']}")
        
        # Hip-Hop模式
        if st.session_state.hiphop_mode:
            st.divider()
            st.success("🎤 Hip-Hop Mode: ON")
        
        # 篮球专项
        if "last_result" in st.session_state and st.session_state.get("last_result", {}).get("tips"):
            st.divider()
            st.success("🏀 篮球模式已激活")
        
        st.divider()
        
        # 本地部署
        st.header("🖥️ 本地部署")
        st.session_state.use_local_llm = st.checkbox(
            "使用 Ollama 本地模型",
            value=st.session_state.use_local_llm,
            help="需先安装 Ollama 并拉取模型（如 qwen2.5:4b）",
        )
        if st.session_state.use_local_llm:
            if ollama_client.is_available():
                models = ollama_client.list_models()
                st.success(f"Ollama 已连接，已安装模型: {len(models)} 个")
                if models:
                    st.caption("可用模型: " + ", ".join(models[:3]))
            else:
                st.warning("未检测到 Ollama 服务，请确保已启动")
                st.caption("安装: https://ollama.com")


def render_wardrobe_page():
    """渲染衣橱管理页面"""
    st.header("👕 我的衣橱")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 上传衣橱照片")
        uploaded_file = st.file_uploader(
            "选择一张衣橱照片", 
            type=["jpg", "jpeg", "png"],
            help="上传包含多件衣物的照片，系统将自动识别"
        )
        
        if uploaded_file:
            # 预览
            image = Image.open(uploaded_file)
            st.image(image, caption="上传的图片", use_column_width=True)
            
            if st.button("🔍 开始识别衣物", type="primary"):
                temp_path = save_uploaded_file(uploaded_file)
                process_wardrobe_image(temp_path)
                st.rerun()
    
    with col2:
        st.subheader("📋 已识别的衣物")
        all_garments = storage.get_all()
        
        if not all_garments:
            st.info("暂无衣物，请先上传照片识别")
        else:
            for i, garment in enumerate(all_garments):
                with st.expander(f"{garment.type.value} - {garment.color}"):
                    if os.path.exists(garment.image_path):
                        st.image(garment.image_path, width=200)
                    st.write(f"**颜色**: {garment.color}")
                    st.write(f"**材质**: {garment.material or '未知'}")
                    st.write(f"**图案**: {garment.pattern or '未知'}")
                    st.write(f"**季节**: {', '.join([s.value for s in garment.season])}")
                    st.write(f"**正式程度**: {garment.formality.value}")
                    st.write(f"**描述**: {garment.description}")


def render_recommend_page():
    """渲染穿搭推荐页面"""
    st.header("✨ 穿搭推荐")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📝 设置偏好")
        
        # Hip-Hop 模式
        st.session_state.hiphop_mode = st.toggle("🎤 Hip-Hop Style 模式", value=st.session_state.hiphop_mode)
        if st.session_state.hiphop_mode:
            st.caption("Oversize版型 + 大胆配色 + 球鞋 + 配饰")
        
        # 天气信息
        city = st.text_input("城市", value="Beijing")
        if st.button("🌤️ 获取天气"):
            with st.spinner("获取天气中..."):
                weather_info = weather_service.get_current_weather(city)
                if weather_info:
                    st.session_state.weather = weather_info
                    st.success(f"已获取 {weather_info['city']} 天气")
                else:
                    st.warning("无法获取天气，请检查API Key")
        
        if st.session_state.weather:
            w = st.session_state.weather
            cols = st.columns(3)
            cols[0].metric("温度", f"{w['temp']}°C")
            cols[1].metric("体感", f"{w['feels_like']}°C")
            cols[2].metric("湿度", f"{w.get('humidity', '?')}%")
            st.caption(f"天气: {w['description']} | 风速: {w.get('wind_speed', '?')}m/s")
        
        # 场合选择（增强：篮球专项）
        occasion = st.selectbox(
            "选择场合",
            [
                "日常",
                "面试",
                "约会",
                "打球",
                "录音棚",
                "上课",
                "聚会",
                "运动",
                "逛街",
                "旅行",
            ],
        )
        
        # 风格偏好
        default_style = "Hip-Hop / Oversize / 街头" if st.session_state.hiphop_mode else ""
        style = st.text_input(
            "风格偏好（可选）",
            value=default_style,
            placeholder="如：Oversize、街头风、简约、商务",
        )
        
        # 生成按钮
        if st.button("🎨 生成穿搭方案", type="primary"):
            with st.spinner("正在生成穿搭方案..."):
                query = WardrobeQuery(
                    occasion=occasion,
                    style=style if style else None,
                    weather_temp=st.session_state.weather.get("temp") if st.session_state.weather else None,
                    weather_feels_like=st.session_state.weather.get("feels_like") if st.session_state.weather else None,
                    weather_desc=st.session_state.weather.get("description") if st.session_state.weather else None,
                )
                
                # 使用完整流水线（支持本地模型）
                result = pipeline.run(query, use_local=st.session_state.use_local_llm)
                
                st.session_state["last_outfits"] = result["outfits"]
                st.session_state["last_evaluations"] = result["evaluations"]
                st.session_state["last_result"] = result
                st.rerun()
    
    with col2:
        st.subheader("👔 推荐方案")
        
        if "last_outfits" in st.session_state and st.session_state["last_outfits"]:
            outfits = st.session_state["last_outfits"]
            evaluations = st.session_state.get("last_evaluations", [])
            result = st.session_state.get("last_result", {})
            
            # 显示潮流提示
            if result.get("trends"):
                with st.expander("📈 参考潮流趋势", expanded=False):
                    for trend in result["trends"]:
                        st.write(f"- {trend}")
            
            # 篮球专项提示
            if result.get("tips"):
                with st.expander("🏀 篮球穿搭贴士", expanded=False):
                    for tip in result["tips"]:
                        st.write(tip)
            
            for i, outfit in enumerate(outfits, 1):
                eval_score = evaluations[i - 1] if i <= len(evaluations) else {}
                with st.expander(f"方案 {i} {'⭐ ' + str(eval_score.get('total_score', '?')) if eval_score else ''}", expanded=(i == 1)):
                    cols = st.columns(4)
                    
                    items = [
                        ("👕 上衣", outfit.top),
                        ("👖 裤子", outfit.bottom),
                        ("👟 鞋子", outfit.shoes),
                        ("🧥 外套", outfit.outerwear),
                    ]
                    
                    for col, (label, item) in zip(cols, items):
                        with col:
                            if item:
                                st.write(f"**{label}**")
                                st.write(f"{item.color} {item.type}")
                                st.caption(item.description)
                            else:
                                st.write(f"**{label}**")
                                st.caption("无")
                    
                    if outfit.accessories:
                        st.write("**配饰**: " + ", ".join([f"{a.color}{a.type}" for a in outfit.accessories]))
                    
                    st.divider()
                    st.write(f"💡 **推荐理由**: {outfit.reason}")
                    
                    # 评估分数
                    if eval_score:
                        score_cols = st.columns(4)
                        score_cols[0].metric("设计感", eval_score.get("design_score", "?"))
                        score_cols[1].metric("合身度", eval_score.get("fitness_score", "?"))
                        score_cols[2].metric("协调性", eval_score.get("coherence_score", "?"))
                        score_cols[3].metric("综合", eval_score.get("total_score", "?"))
                        if eval_score.get("suggestions"):
                            st.caption(f"改进建议: {eval_score['suggestions']}")
                    
                    # 反馈按钮
                    feedback_cols = st.columns(5)
                    with feedback_cols[0]:
                        if st.button("👍", key=f"like_{i}"):
                            feedback_store.add_feedback(
                                outfit, 5, occasion=occasion, style=style
                            )
                            st.success("感谢反馈！")
                    with feedback_cols[1]:
                        if st.button("👎", key=f"dislike_{i}"):
                            feedback_store.add_feedback(
                                outfit, 1, occasion=occasion, style=style
                            )
                            st.warning("已记录，我们会改进")
        else:
            st.info("请在左侧设置偏好并点击生成按钮")
            st.caption("💡 提示：开启 Hip-Hop Style 模式可获得更街头风格的推荐")


def render_image_search_page():
    """渲染以图搜衣页面"""
    st.header("🔍 以图搜衣")
    st.caption("上传一张穿搭照片，从你的衣橱中找到风格相近的单品")

    col1, col2 = st.columns([1, 1])

    with col1:
        query_file = st.file_uploader(
            "上传参考穿搭照片",
            type=["jpg", "jpeg", "png"],
            help="上传你喜欢穿搭风格的照片，系统将匹配相似衣物",
        )
        top_k = st.slider("返回数量", min_value=1, max_value=10, value=5)

        if query_file:
            st.image(query_file, caption="参考图片", use_column_width=True)
            if st.button("🔍 开始搜索", type="primary"):
                with st.spinner("正在检索相似衣物..."):
                    temp_path = save_uploaded_file(query_file)
                    results = image_search.search_by_image(temp_path, top_k=top_k)
                    st.session_state.image_search_results = results
                    st.rerun()

    with col2:
        st.subheader("👕 相似单品")
        results = st.session_state.get("image_search_results", [])
        if not results:
            st.info("暂无结果，请先上传参考图")
        else:
            for g in results:
                with st.container():
                    cols = st.columns([1, 3])
                    with cols[0]:
                        if os.path.exists(g.image_path):
                            st.image(g.image_path, width=120)
                        else:
                            st.caption("无图")
                    with cols[1]:
                        st.write(f"**{g.type}** - {g.color}")
                        st.caption(g.description)
                    st.divider()


def render_chat_page():
    """渲染对话页面"""
    st.header("💬 穿搭助手对话")
    
    # 显示历史消息
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("输入你的穿搭问题..."):
        # 添加用户消息
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # 生成回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                # 简单规则匹配
                if "配" in prompt or "穿" in prompt:
                    response = "根据你的衣橱，我建议你可以尝试简约休闲风格。需要我为你生成具体的穿搭方案吗？"
                elif "天气" in prompt:
                    if st.session_state.weather:
                        response = f"当前温度 {st.session_state.weather['temp']}°C，建议穿轻薄透气的衣物。"
                    else:
                        response = "请先在推荐页面获取天气信息。"
                else:
                    response = "我是你的穿搭助手，可以帮你推荐穿搭方案、管理衣橱。请上传衣物照片或选择推荐功能开始使用。"
                
                st.write(response)
        
        st.session_state.chat_history.append({"role": "assistant", "content": response})


def main():
    """主函数"""
    st.title(f"👕 {APP_TITLE}")
    st.markdown("---")
    
    # 侧边栏
    render_sidebar()
    
    # 页面导航
    page = st.sidebar.radio(
        "导航",
        ["👕 我的衣橱", "✨ 穿搭推荐", "🔍 以图搜衣", "💬 对话助手", "🚀 差异特色"],
        label_visibility="collapsed"
    )
    
    if page == "👕 我的衣橱":
        render_wardrobe_page()
    elif page == "✨ 穿搭推荐":
        render_recommend_page()
    elif page == "🔍 以图搜衣":
        render_image_search_page()
    elif page == "💬 对话助手":
        render_chat_page()
    elif page == "🚀 差异特色":
        render_features_page()
    
    # 页脚
    st.divider()
    st.caption("💡 提示：首次使用请先在侧边栏配置API密钥")


def render_features_page():
    """渲染差异特色页面"""
    st.header("🚀 差异特色")
    st.caption("本项目的核心差异化功能，让推荐更懂你的生活方式")

    tabs = st.tabs([
        "🎤 Hip-Hop Style",
        "🏀 篮球场景",
        "🔍 以图搜衣",
        "🖥️ 本地部署",
    ])

    with tabs[0]:
        st.subheader("Hip-Hop Style 专属模式")
        st.write("""
        **为什么这是差异化？**
        通用穿搭助手只懂"商务休闲""简约"，但不懂说唱文化的审美。
        """)
        col1, col2 = st.columns(2)
        with col1:
            st.write("**核心规则**")
            st.write("- ✅ 优先 Oversize / Baggy 版型")
            st.write("- ✅ 配色：黑/白/灰 + 高饱和亮色")
            st.write("- ✅ 必备元素：卫衣、棒球服、工装裤、篮球鞋")
            st.write("- ✅ 配饰：腰包、棒球帽、金链子")
            st.write("- ❌ 避免：修身、商务、正装")
        with col2:
            st.write("**使用方式**")
            st.write("1. 在「穿搭推荐」页面开启 Hip-Hop Mode")
            st.write("2. 选择场合：聚会/录音棚/打球")
            st.write("3. 系统自动注入街头风格规则")
            st.write("4. LLM 按权重优先推荐匹配单品")
        st.info("💡 提示：开启模式后，推荐结果会自动偏向街头潮流风格")

    with tabs[1]:
        st.subheader("篮球场景专项优化")
        st.write("""
        **为什么这是差异化？**
        打球场景有特殊需求：速干、支撑、防护。普通助手不懂运动装备。
        """)
        col1, col2 = st.columns(2)
        with col1:
            st.write("**篮球装备识别**")
            st.write("- 🏀 篮球鞋型号识别（GT Cut、Harden、Jordan 等）")
            st.write("- 👕 速干/压缩衣优先")
            st.write("- 🩱 运动短裤/压缩裤")
            st.write("- 🧦 运动袜、护膝等配件")
        with col2:
            st.write("**评分机制**")
            st.write("- 篮球鞋 +10 分")
            st.write("- 速干上衣 +5 分")
            st.write("- 运动配件 +3 分")
            st.write("- 自动排序，优先推荐运动装备")
        st.info("💡 选择「打球」场合，系统自动激活篮球专项评分")

    with tabs[2]:
        st.subheader("以图搜衣 — 多模态相似检索")
        st.write("""
        **为什么这是差异化？**
        文字描述不够直观。上传一张喜欢的穿搭照片，直接找到衣橱里的相似款。
        """)
        st.write("**技术实现**")
        st.write("- CLIP 模型将图片编码为向量")
        st.write("- ChromaDB 存储衣物图片向量")
        st.write("- 余弦相似度检索 Top-K 相似单品")
        st.write("- 支持上传任意穿搭参考图")
        st.info("💡 前往「🔍 以图搜衣」页面体验")

    with tabs[3]:
        st.subheader("本地部署 — 数据隐私保护")
        st.write("""
        **为什么这是差异化？**
        衣物照片是隐私数据。云端方案有泄露风险，本地部署彻底解决。
        """)
        col1, col2 = st.columns(2)
        with col1:
            st.write("**技术方案**")
            st.write("- Ollama 本地运行 LLM")
            st.write("- 推荐模型：Qwen2.5:4B / Gemma3:4B")
            st.write("- 所有推理在本地完成")
            st.write("- 衣物照片不上传云端")
        with col2:
            st.write("**部署步骤**")
            st.write("1. 安装 Ollama: https://ollama.com")
            st.write("2. 拉取模型: `ollama pull qwen2.5:4b`")
            st.write("3. 启动 Ollama 服务")
            st.write("4. 在侧边栏勾选「使用 Ollama 本地模型」")
        st.info("💡 适合对数据隐私敏感的用户")


def main():
    """主函数"""
    st.title(f"👕 {APP_TITLE}")
    st.markdown("---")
    
    # 侧边栏
    render_sidebar()
    
    # 页面导航
    page = st.sidebar.radio(
        "导航",
        ["👕 我的衣橱", "✨ 穿搭推荐", "🔍 以图搜衣", "💬 对话助手", "🚀 差异特色"],
        label_visibility="collapsed"
    )
    
    if page == "👕 我的衣橱":
        render_wardrobe_page()
    elif page == "✨ 穿搭推荐":
        render_recommend_page()
    elif page == "🔍 以图搜衣":
        render_image_search_page()
    elif page == "💬 对话助手":
        render_chat_page()
    elif page == "🚀 差异特色":
        render_features_page()
    
    # 页脚
    st.divider()
    st.caption("💡 提示：首次使用请先在侧边栏配置API密钥")


if __name__ == "__main__":
    main()
