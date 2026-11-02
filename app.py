import streamlit as st

# 从各个模块文件引入渲染函数
from modules import mod_world, mod_plot, mod_archive, mod_llm
# 引入启动时读取记忆的工具
from utils import load_memory

st.set_page_config(page_title="虚构世界观引擎", layout="wide")

# ==========================================
# 0. 全局大脑初始化
# ==========================================
# 使用 load_memory() 替换空字典进行初始化，以保证本地硬盘数据的加载。
if "compiler_memory" not in st.session_state:
    st.session_state.compiler_memory = load_memory()
if "history_outputs" not in st.session_state:
    st.session_state.history_outputs = []
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# ==========================================
# 🎛️ 侧边栏：模块总开关与模型设置
# ==========================================
st.sidebar.title("🎛️ 模块仪表盘")
enable_wb = st.sidebar.toggle("📝 世界观设定录入", value=True, disabled=st.session_state.is_generating)
enable_plot = st.sidebar.toggle("🤖 智能剧情与回溯", value=True, disabled=st.session_state.is_generating)
enable_archive = st.sidebar.toggle("🗄️ 当前档案库", value=False, disabled=st.session_state.is_generating)
enable_llm = st.sidebar.toggle("⚖️ 大模型推演生成", value=True, disabled=st.session_state.is_generating)

st.sidebar.divider()
st.sidebar.header("🔌 模型接入设置")

api_choice = st.sidebar.radio(
    "大模型运行模式：", 
    ["☁️ 云端 API (DeepSeek)", "🦙 Ollama 本地托管服务", "📁 本地绝对地址直接加载 (GGUF)"],
    disabled=st.session_state.is_generating
)

api_key = ""
ollama_model = ""
gguf_path = ""

if api_choice == "☁️ 云端 API (DeepSeek)":
    api_key = st.sidebar.text_input("🔑 API Key:", type="password", disabled=st.session_state.is_generating)
elif api_choice == "🦙 Ollama 本地托管服务":
    ollama_model = st.sidebar.text_input("🦙 本地模型名称:", value="deepseek-r1:14b", disabled=st.session_state.is_generating)
else:
    gguf_path = st.sidebar.text_input("📂 模型绝对路径 (.gguf):", value=r"D:\Models\deepseek-r1-14b.gguf", disabled=st.session_state.is_generating)

# ==========================================
# 🖥️ 主界面：瀑布流装配车间
# ==========================================
# 以下部分按条件渲染已启用的对应模块。
if enable_wb:
    with st.container(border=True):
        mod_world.render()
        
if enable_plot:
    with st.container(border=True):
        mod_plot.render()
        
if enable_archive:
    with st.container(border=True):
        mod_archive.render()
        

if enable_llm:
    with st.container(border=True):
        # 将从侧边栏获取到的推演参数向下级传递。
        mod_llm.render(api_choice, api_key, ollama_model, gguf_path)

# ==========================================
# 📜 全局历史推演结果持久化展示区
# ==========================================
if st.session_state.history_outputs:
    st.markdown("---")
    st.markdown("### 📜 历史推演记录与存档")
    if st.button("🧹 清空历史推演记录", key="clear_history_btn", disabled=st.session_state.is_generating):
        st.session_state.history_outputs = []
        st.rerun()
        
    for idx, item in enumerate(reversed(st.session_state.history_outputs)):
        with st.expander(f"📌 推演存档 #{len(st.session_state.history_outputs)-idx} | 输入：{item['input'][:20]}...", expanded=(idx==0)):
            st.markdown(f"**✍️ 玩家输入：**\n> {item['input']}")
            st.markdown(f"**🎬 大模型推演结果：**\n{item['output']}")
