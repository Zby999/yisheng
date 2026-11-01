# ==========================================
# 【模块 1】初始化与侧边栏设置
# ==========================================
import streamlit as st
import requests

if 'compiler_memory' not in st.session_state:
    st.session_state.compiler_memory = {
        "characters": {},
        "factions": {}
    }

st.sidebar.header("🔌 模型接入设置")
api_choice = st.sidebar.radio("选择大模型后端：", ["本地 Ollama (完全离线)", "云端 DeepSeek API"])

if api_choice == "云端 DeepSeek API":
    api_key = st.sidebar.text_input("🔑 请输入 API Key:", type="password")
else:
    ollama_model = st.sidebar.text_input("🦙 本地模型名称:", value="deepseek-r1:8b")
    st.sidebar.caption("请确保 Ollama 软件正在电脑后台运行")

# ==========================================
# 【模块 2】头部 UI
# ==========================================
st.title("我要给TA完整的一生！ ⚙️")
st.write("欢迎来到创作者的专属翻译器！")
st.divider()

# ==========================================
# 【模块 3】设定录入 (分批次、模块化追加版)
# ==========================================
st.subheader("📝 第一步：录入与更新世界观设定")

# ------------------------------------------
# [模块 3.1] 实体定位器：确定你要操作的对象
# ------------------------------------------
st.markdown("#### 🎯 1. 锁定目标实体")
col1, col2 = st.columns(2)
with col1:
    entity_type = st.selectbox("选择操作类型", ["characters", "factions"], format_func=lambda x: "🎭 角色" if x=="characters" else "🏛️ 组织/势力")
with col2:
    # 只要填了名字就可以开始操作
    entity_name = st.text_input("实体名称*", placeholder="例如: 黑时满", help="输入新名称即为创建；输入已有名称即为追加设定。")

# 实时检测该实体是否已存在，并给出反馈
is_existing = entity_name in st.session_state.compiler_memory[entity_type]
if entity_name:
    if is_existing:
        st.info(f"💡 系统检测到已有 [{entity_name}]，接下来的保存将为其 **追加/覆盖** 属性。")
    else:
        st.success(f"💡 这是一个全新实体，接下来的保存将为您 **创建** [{entity_name}]。")

# ------------------------------------------
# [模块 3.2] 动态属性编辑器：随时增删的小标签
# ------------------------------------------
st.markdown("#### ✨ 2. 追加/修改属性标签")
st.caption("提示：无需一次性填完。你可以只填一条，随时回来继续追加。")

if 'attr_count' not in st.session_state:
    st.session_state.attr_count = 1

custom_attrs = []
for i in range(st.session_state.attr_count):
    col_k, col_v = st.columns(2)
    with col_k:
        k = st.text_input(f"属性标签 {i+1}", key=f"custom_k_{i}", placeholder="例如: 核心动机 / 隐藏创伤")
    with col_v:
        v = st.text_input(f"属性内容 {i+1}", key=f"custom_v_{i}", placeholder="例如: 打破循环 / 目睹法则失控")
    custom_attrs.append((k, v))

if st.button("➕ 增加一个新属性槽位"):
    st.session_state.attr_count += 1
    st.rerun()

# ------------------------------------------
# [模块 3.3] 长文本与保存逻辑：智能拼装数据
# ------------------------------------------
st.markdown("#### 📖 3. 详细背景补全 (选填)")
free_text = st.text_area("大段背景资料", placeholder="随时把想到的长篇大论粘贴进来，系统会自动将其拼接到现有背景之后...")

if st.button("💾 保存/更新 设定到数据库", type="primary"):
    if entity_name:
        # 如果是新实体，先初始化一个空档案袋
        if not is_existing:
            st.session_state.compiler_memory[entity_type][entity_name] = {}
        
        # 遍历动态标签，追加到该实体下
        for key, value in custom_attrs:
            if key and value:  
                st.session_state.compiler_memory[entity_type][entity_name][key] = value
        
        # 处理长文本追加逻辑
        if free_text: 
            old_text = st.session_state.compiler_memory[entity_type][entity_name].get("详细背景", "")
            if old_text:
                # 换行追加，保护历史数据
                st.session_state.compiler_memory[entity_type][entity_name]["详细背景"] = old_text + "\n\n" + free_text
            else:
                st.session_state.compiler_memory[entity_type][entity_name]["详细背景"] = free_text
        
        # 保存成功后，输入框重置为1行
        st.session_state.attr_count = 1
        st.success(f"成功！[{entity_name}] 的档案已更新。")
    else:
        st.warning("⚠️ 必须填写【实体名称】才能执行操作！")

# ------------------------------------------
# [模块 3.4] 批量导入与导出设定 (同人文/跑团福音)
# ------------------------------------------
import json

st.markdown("#### 📥 4. 批量导入/导出设定集")
st.caption("不想手动录入？直接分享或上传设定文件！跑团模组、同人设定一键加载。")

file_col1, file_col2 = st.columns(2)

with file_col1:
    # 导出当前设定的功能
    current_data = json.dumps(st.session_state.compiler_memory, ensure_ascii=False, indent=2)
    st.download_button(
        label="⬇️ 导出当前世界观档案 (.json)",
        data=current_data,
        file_name="my_world_settings.json",
        mime="application/json",
        help="将你目前录入的所有设定下载为文件，发给朋友，他们就可以直接导入了！"
    )

with file_col2:
    # 导入设定的功能
    uploaded_file = st.file_uploader("📂 上传现有的设定集文件 (.json)", type=["json"], label_visibility="collapsed")
    if uploaded_file is not None:
        if st.button("🚀 确认合并导入", type="primary"):
            try:
                imported_data = json.load(uploaded_file)
                # 遍历合并数据，保护现有的其他数据不被清空
                for entity_type in ["characters", "factions"]:
                    if entity_type in imported_data:
                        for name, attrs in imported_data[entity_type].items():
                            st.session_state.compiler_memory[entity_type][name] = attrs
                st.success("🎉 设定集导入成功！请查看下方【档案库】。")
            except Exception as e:
                st.error(f"导入失败，文件格式不匹配。详情: {e}")

# ------------------------------------------
# [模块 3.5] 文本智能解析录入 (第一阶段：界面与框架)
# ------------------------------------------
st.markdown("#### 🤖 5. 智能解析录入 (测试中)")
st.caption("直接粘贴大段小说原文或人物小传，让 AI 自动帮你提取角色和阵营设定！")

raw_text_input = st.text_area("📋 粘贴原始设定文本：", placeholder="例如：黑时满，隶属于晶体管研讨会。他是个试图打破循环的观测者，随身带着一块停滞的怀表...")

if st.button("✨ 自动提取并合并到档案库"):
    if not raw_text_input:
        st.warning("请先粘贴一段设定文本！")
    else:
        st.info("系统提示：UI 入口已打通，即将在此处接入大模型解析逻辑...")
        # 预留给第二步的开发空间
        # 1. 组装专门用于“提取信息”的 Prompt
        # 2. 调用 API 将 raw_text_input 转换成 JSON 字典
        # 3. 将解析出来的字典写入 st.session_state.compiler_memory

st.divider()

# ==========================================
# 【模块 4】档案库展示与删除
# ==========================================
st.subheader("🗄️ 当前世界观档案库")
st.write("在这里可以查看或删除已录入的设定：")

st.markdown("### 🎭 角色档案")
if st.session_state.compiler_memory["characters"]:
    for char_name, attrs in list(st.session_state.compiler_memory["characters"].items()):
        with st.expander(f"👤 {char_name}"):
            for key, value in attrs.items():
                st.markdown(f"- **{key}**: {value}")
            if st.button(f"🗑️ 删除角色 [{char_name}]", key=f"del_char_{char_name}"):
                del st.session_state.compiler_memory["characters"][char_name]
                st.rerun()
else:
    st.info("暂无角色数据，请在上方录入。")

st.markdown("### 🏛️ 组织/势力档案")
if st.session_state.compiler_memory["factions"]:
    for faction_name, attrs in list(st.session_state.compiler_memory["factions"].items()):
        with st.expander(f"🚩 {faction_name}"):
            for key, value in attrs.items():
                st.markdown(f"- **{key}**: {value}")
            if st.button(f"🗑️ 删除组织 [{faction_name}]", key=f"del_fac_{faction_name}"):
                del st.session_state.compiler_memory["factions"][faction_name]
                st.rerun()
else:
    st.info("暂无组织数据，请在上方录入。")

st.divider()

# ==========================================
# 【模块 5】意图判定与大模型调用 (全面子模块化版)
# ==========================================
st.subheader("⚖️ 第二步：意图判定与推演生成")

# ------------------------------------------
# [模块 5.1] 用户输入与参数设定
# ------------------------------------------
user_input = st.text_area("✍️ 玩家/读者最新输入剧情：", "我掏出枪，试图砸毁这台晶体管计算机，强行终止死亡回溯！")

col3, col4, col5 = st.columns(3)
with col3:
    world_impact = st.slider("🌍 世界观破坏度", 1, 10, 8)
with col4:
    ooc_risk = st.slider("🎭 OOC 偏离风险", 1, 10, 5)
with col5:
    intensity = st.slider("🔥 动作激烈程度", 1, 10, 9)

# ------------------------------------------
# [模块 5.2] 指令编译与免流转复制
# ------------------------------------------
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    generate_only = st.button("👁️ 仅生成提示词 (免费复制测试)")
with btn_col2:
    send_api = st.button("⚡ 编译并发送给大模型")

if generate_only or send_api:
    if not user_input:
        st.warning("请先输入玩家的动作！")
    else:
        # 组装最终发给大模型的提示词
        final_prompt = f"""【系统级别指令：严格扮演与推演控制】
一、当前世界观与出场角色设定库：\n{st.session_state.compiler_memory}
二、评估参数：
- 世界观破坏度：{world_impact}/10
- 人设偏离风险：{ooc_risk}/10
- 动作激烈程度：{intensity}/10
三、强制规则：若破坏度>7排斥反应；若激烈度>7采用高压短句文风。
四、读者最新动作/台词：\n“{user_input}”
请直接生成接下来的剧情回应："""
        
        st.info("💡 提示：将鼠标悬停在下方黑色代码框的 **右上角**，点击【复制】图标即可一键复制全部提示词。")
        st.code(final_prompt, language="markdown")

        # ------------------------------------------
        # [模块 5.3] 大模型网络请求逻辑
        # ------------------------------------------
        if send_api:
            st.subheader("🎬 大模型推演结果：")
            
            if api_choice == "本地 Ollama (完全离线)":
                with st.spinner("Ollama 正在本地显卡上疯狂运算中..."):
                    try:
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json={"model": ollama_model, "prompt": final_prompt, "stream": False}
                        )
                        if response.status_code == 200:
                            st.write(response.json().get("response", ""))
                        else:
                            st.error(f"调用失败，状态码: {response.status_code}")
                    except Exception as e:
                        st.error(f"连接 Ollama 失败，请确认后台运行。详情: {e}")
            
            elif api_choice == "云端 DeepSeek API":
                if not api_key:
                    st.error("请先在左侧侧边栏填入 API Key！")
                else:
                    with st.spinner("正在呼叫云端 DeepSeek 服务器..."):
                        try:
                            response = requests.post(
                                "https://api.deepseek.com/chat/completions",
                                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": final_prompt}], "stream": False}
                            )
                            if response.status_code == 200:
                                st.write(response.json()["choices"][0]["message"]["content"])
                            else:
                                st.error(f"API 调用失败。错误信息: {response.text}")
                        except Exception as e:
                            st.error(f"网络连接出错: {e}")