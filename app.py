import streamlit as st
import requests
import json
import re

# ==========================================
# 0. 全局初始化与配置
# ==========================================
st.set_page_config(page_title="虚构世界观与角色设定编译器", layout="wide")

if "compiler_memory" not in st.session_state:
    st.session_state.compiler_memory = {
        "characters": {},
        "factions": {},
        "raw_plot_pool": []
    }

if "history_outputs" not in st.session_state:
    st.session_state.history_outputs = []

# 【新增锁状态】：用于在生成时禁用页面交互，防止切走或误触导致中断
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

char_count = len(st.session_state.compiler_memory.get("characters", {}))
faction_count = len(st.session_state.compiler_memory.get("factions", {}))
plot_count = len(st.session_state.compiler_memory.get("raw_plot_pool", []))

# ==========================================
# 🧩 可复用的“双链悬浮联想”检索组件函数
# ==========================================
def render_bi_link_search_box(input_label, input_key, help_text=""):
    query_text = st.text_input(input_label, placeholder="输入关键词（如：石满、不周山）...", key=input_key, help=help_text, disabled=st.session_state.is_generating)
    
    if query_text:
        memory = st.session_state.compiler_memory
        matched_results = []
        
        for c_name, c_attrs in memory.get("characters", {}).items():
            if query_text in c_name or any(query_text in str(v) for v in c_attrs.values()):
                matched_results.append(("角色", c_name, c_attrs))
                
        for f_name, f_attrs in memory.get("factions", {}).items():
            if query_text in f_name or any(query_text in str(v) for v in f_attrs.values()):
                matched_results.append(("势力", f_name, f_attrs))
                
        for idx, plot in enumerate(memory.get("raw_plot_pool", [])):
            if query_text in plot:
                matched_results.append(("剧情切片", f"片段 {idx+1}", {"原文内容": plot}))

        if matched_results:
            st.info(f"💡 双链联想：检测到 {len(matched_results)} 个相关历史词条，展开可查看预览：")
            for item_type, title, content_dict in matched_results:
                with st.expander(f"📌 [{item_type}] {title} （点击展开悬浮预览）"):
                    for k, v in content_dict.items():
                        st.markdown(f"**{k}**: {v}")
        else:
            st.caption("✨ 暂未发现历史关联词条，这将是一个全新的原创双链节点。")
            
    return query_text

# ==========================================
# 🧭 侧边栏：核心导航菜单与模型设置
# ==========================================
st.sidebar.title("🧭 导航菜单")

nav_module = st.sidebar.radio(
    "功能模块选择：",
    [
        "📝 世界观设定录入", 
        "🤖 智能剧情与回溯", 
        "🗄️ 当前档案库 (带分页)", 
        "🔍 知识图谱与双链搜索",
        "⚖️ 大模型推演生成"
    ],
    disabled=st.session_state.is_generating  # 生成时锁定侧边栏，防止切走
)

st.sidebar.divider()
st.sidebar.header("🔌 模型接入设置")
api_choice = st.sidebar.radio("选择大模型后端：", ["本地 Ollama (完全离线)", "云端 DeepSeek API"], disabled=st.session_state.is_generating)

if api_choice == "云端 DeepSeek API":
    api_key = st.sidebar.text_input("🔑 请输入 API Key:", type="password", disabled=st.session_state.is_generating)
else:
    ollama_model = st.sidebar.text_input("🦙 本地模型名称:", value="deepseek-r1:14b", disabled=st.session_state.is_generating)
    st.sidebar.caption("请确保 Ollama 软件正在电脑后台运行")


# ==========================================
# 🖥️ 主界面：根据侧边栏选项动态切换模块
# ==========================================

if nav_module == "📝 世界观设定录入":
    st.title("📖 世界观与角色百科词条录入")
    st.write("自由构建立体词条：通过多维卡片，将小标题、核心关键词与详细正文挂载！")
    st.divider()

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        entry_category = st.selectbox(
            "🏷️ 词条分类", 
            ["characters", "factions", "world_concepts"], 
            format_func=lambda x: "🎭 角色人物" if x=="characters" else ("🏛️ 组织阵营" if x=="factions" else "🌍 世界观概念/地点"),
            disabled=st.session_state.is_generating
        )
    with col_t2:
        entry_name = render_bi_link_search_box(
            input_label="📌 词条名称（如：角色姓名、组织姓名、地点名称……）*", 
            input_key="wiki_entry_name_input", 
            help_text="输入名称后检索全库，避免重名或设定冲突"
        )

    st.markdown("---")
    st.markdown("#### 🧩 多维特性与模块化卡片")

    session_key = f"cards_{entry_name if entry_name else 'default'}"
    if session_key not in st.session_state:
        st.session_state[session_key] = [
            {"sub_title": "核心身份与动机", "keywords": "时间回溯, 观测者", "content": ""}
        ]

    cards = st.session_state[session_key]
    updated_cards = []
    for idx, card in enumerate(cards):
        with st.container():
            st.markdown(f"**📌 维度模块 #{idx+1}**")
            c_col1, c_col2 = st.columns([1, 1])
            with c_col1:
                sub_title = st.text_input(f"小标题名称 #{idx+1}", value=card["sub_title"], key=f"sub_{idx}", disabled=st.session_state.is_generating)
            with c_col2:
                keywords = st.text_input(f"核心关键词/标签 #{idx+1} (用逗号分隔)", value=card["keywords"], key=f"kw_{idx}", disabled=st.session_state.is_generating)
            
            content = st.text_area(f"详细正文说明 #{idx+1}", value=card["content"], key=f"cnt_{idx}", height=90, disabled=st.session_state.is_generating)
            
            if len(cards) > 1:
                if st.button(f"🗑️ 删除该模块 #{idx+1}", key=f"del_card_{idx}", disabled=st.session_state.is_generating):
                    cards.pop(idx)
                    st.rerun()
            st.markdown("---")
            updated_cards.append({"sub_title": sub_title, "keywords": keywords, "content": content})
            
    st.session_state[session_key] = updated_cards

    if st.button("➕ 添加一个新的维度模块卡片", disabled=st.session_state.is_generating):
        st.session_state[session_key].append({"sub_title": "", "keywords": "", "content": ""})
        st.rerun()

    if st.button("💾 归档并保存该立体百科词条", type="primary", use_container_width=True, disabled=st.session_state.is_generating):
        if entry_name:
            if entry_category not in st.session_state.compiler_memory:
                st.session_state.compiler_memory[entry_category] = {}
            
            entry_data = {}
            for card in st.session_state[session_key]:
                if card["sub_title"]:
                    entry_data[card["sub_title"]] = {
                        "keywords": [kw.strip() for kw in card["keywords"].split(",") if kw.strip()],
                        "content": card["content"]
                    }
            
            st.session_state.compiler_memory[entry_category][entry_name] = entry_data
            st.success(f"🎉 包含多维模块的词条【{entry_name}】已成功写入世界观百科库！")
            st.rerun()
        else:
            st.warning("⚠️ 必须填写【词条名称】才能保存！")

elif nav_module == "🤖 智能剧情与回溯":
    st.title("🤖 智能剧情回溯与自动归档中心")
    st.divider()
    if "raw_plot_pool" not in st.session_state.compiler_memory:
        st.session_state.compiler_memory["raw_plot_pool"] = []

    new_plot_text = st.text_area("📋 随时随地粘贴剧情/随笔原文：", height=150, disabled=st.session_state.is_generating)
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("📥 存入剧情池", disabled=st.session_state.is_generating):
            if new_plot_text:
                st.session_state.compiler_memory["raw_plot_pool"].append(new_plot_text)
                st.success("🎉 剧情已成功存入公用池！")
                st.rerun()
            else:
                st.warning("请输入内容！")
    with col_p2:
        if st.button("🔄 全局刷新：用最新角色库扫描并归档", type="primary", disabled=st.session_state.is_generating):
            pool = st.session_state.compiler_memory.get("raw_plot_pool", [])
            characters = st.session_state.compiler_memory.get("characters", {})
            match_count = 0
            for char_name in characters:
                characters[char_name]["自动关联剧情"] = []
            for plot in pool:
                for char_name in characters:
                    if char_name in plot:
                        if "自动关联剧情" not in characters[char_name]: characters[char_name]["自动关联剧情"] = []
                        if plot not in characters[char_name]["自动关联剧情"]:
                            characters[char_name]["自动关联剧情"].append(plot)
                            match_count += 1
            st.success(f"✨ 全局刷新完毕！完成 {match_count} 处自动关联归档！")

elif nav_module == "🗄️ 当前档案库 (带分页)":
    st.title(f"🗄️ 世界观档案库总览 (角色: {char_count} | 势力: {faction_count})")
    st.divider()
    def render_pagination_list(items_dict, category_name, items_per_page=3):
        st.markdown(f"### 🎭 {category_name}")
        if not items_dict: return
        item_keys = list(items_dict.keys())
        total_pages = (len(item_keys) + items_per_page - 1) // items_per_page
        page_key = f"page_{category_name}"
        if page_key not in st.session_state: st.session_state[page_key] = 1
        
        for name in item_keys[(st.session_state[page_key]-1)*items_per_page : st.session_state[page_key]*items_per_page]:
            with st.expander(f"👤 {name}"):
                for key, value in items_dict[name].items():
                    st.markdown(f"- **{key}**: {value}")
                if st.button(f"🗑️ 删除 [{name}]", key=f"del_{category_name}_{name}", disabled=st.session_state.is_generating):
                    del items_dict[name]
                    st.rerun()

    render_pagination_list(st.session_state.compiler_memory["characters"], "角色档案", items_per_page=3)
    render_pagination_list(st.session_state.compiler_memory["factions"], "组织/势力档案", items_per_page=3)

elif nav_module == "🔍 知识图谱与双链搜索":
    st.title("🔍 全局双链搜索与词条聚合中心")
    search_query = st.text_input("🔎 输入想要双链检索的关键词：", disabled=st.session_state.is_generating)
    if search_query:
        for c_name, c_attrs in st.session_state.compiler_memory["characters"].items():
            if search_query in c_name or any(search_query in str(v) for v in c_attrs.values()):
                with st.expander(f"🎭 关联角色: {c_name}"):
                    for k, v in c_attrs.items(): st.markdown(f"- **{k}**: {v}")
            
elif nav_module == "⚖️ 大模型推演生成":
    st.title("⚖️ 大模型推演生成中心")
    st.write("在这里输入玩家/读者最新的剧情走向，结合已编译的世界观设定库进行大模型实时推演。")
    st.divider()

    # 当处于生成状态时，输入框和滑块被自动禁用，防止用户误触
    user_input = st.text_area(
        "✍️ 玩家/读者最新输入剧情：",
        "我掏出枪，试图砸毁这台晶体管计算机，强行终止死亡回溯！", 
        height=120,
        disabled=st.session_state.is_generating
    )

    col3, col4, col5 = st.columns(3)
    with col3:
        world_impact = st.slider("🌍 世界观破坏度", 1, 10, 8, disabled=st.session_state.is_generating)
    with col4:
        ooc_risk = st.slider("🎭 OOC 偏离风险", 1, 10, 5, disabled=st.session_state.is_generating)
    with col5:
        intensity = st.slider("🔥 动作激烈程度", 1, 10, 9, disabled=st.session_state.is_generating)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        generate_only = st.button("👁️ 仅生成提示词", disabled=st.session_state.is_generating)
    with btn_col2:
        send_api = st.button("⚡ 编译并发送给大模型", disabled=st.session_state.is_generating)

    if generate_only or send_api:
        if not user_input:
            st.warning("请先输入玩家的动作！")
        else:
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

            if send_api:
                # 开启生成状态锁，锁定所有输入，保护流式传输不被切断
                st.session_state.is_generating = True
                st.subheader("🎬 大模型推演结果：")
                
                if api_choice == "本地 Ollama (完全离线)":
                    with st.spinner("Ollama 正在本地显卡上疯狂运算中..."):
                        try:
                            response = requests.post(
                                "http://localhost:11434/api/generate",
                                json={
                                    "model": ollama_model, 
                                    "prompt": final_prompt, 
                                    "stream": True,  # 开启流式
                                    "options": {
                                        "num_predict": 2048,
                                        "temperature": 0.7
                                    }
                                },
                                stream=True 
                            )
                        
                            if response.status_code == 200:
                                full_response = ""
                                output_placeholder = st.empty()
                
                                for line in response.iter_lines():
                                    if line:
                                        body = json.loads(line.decode('utf-8'))
                                        chunk = body.get("response", "")
                                        full_response += chunk
                                        output_placeholder.markdown(full_response + "▌")
                        
                                        if body.get("done", False):
                                            break
                
                                output_placeholder.markdown(full_response)
                                st.session_state.history_outputs.append({
                                    "input": user_input,
                                    "output": full_response
                                })
                                st.success("🎉 推演结果已成功归档保存！")
                            else:
                                st.error(f"调用失败，状态码: {response.status_code}")
                        except Exception as e:
                            st.error(f"连接 Ollama 失败，请确认后台运行。详情: {e}")
                        finally:
                            # 无论成功失败，流式传输结束后立刻解除锁定并刷新页面恢复交互
                            st.session_state.is_generating = False
                            st.rerun()

                elif api_choice == "云端 DeepSeek API":
                    api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
                    if not api_key:
                        st.error("❌ 未检测到本地安全配置（secrets.toml 中的 DEEPSEEK_API_KEY）！")
                        st.session_state.is_generating = False
                    else:
                        with st.spinner("正在呼叫云端 DeepSeek 服务器..."):
                            try:
                                response = requests.post(
                                    "https://api.deepseek.com/chat/completions",
                                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                                    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": final_prompt}], "stream": False}
                                )
                                if response.status_code == 200:
                                    res_text = response.json()["choices"][0]["message"]["content"]
                                    st.session_state.history_outputs.append({
                                        "input": user_input,
                                        "output": res_text
                                    })
                                    st.success("🎉 云端推演结果已成功归档保存！")
                                else:
                                    st.error(f"API 调用失败。错误信息: {response.text}")
                            except Exception as e:
                                st.error(f"网络连接出错: {e}")
                            finally:
                                st.session_state.is_generating = False
                                st.rerun()

# ==========================================
# 📜 历史推演结果持久化展示区
# ==========================================
if st.session_state.history_outputs:
    st.markdown("---")
    st.markdown("### 📜 历史推演记录与存档 (防刷新丢失)")
    if st.button("🧹 清空历史推演记录", key="clear_history_btn", disabled=st.session_state.is_generating):
        st.session_state.history_outputs = []
        st.rerun()
        
    for idx, item in enumerate(reversed(st.session_state.history_outputs)):
        with st.expander(f"📌 推演存档 #{len(st.session_state.history_outputs)-idx} | 输入：{item['input'][:20]}...", expanded=(idx==0)):
            st.markdown(f"**✍️ 玩家输入：**\n> {item['input']}")
            st.markdown(f"**🎬 大模型推演结果：**\n{item['output']}")