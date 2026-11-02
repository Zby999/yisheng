import streamlit as st
import sys
import os

# 确保能找到外层的 utils.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import render_bi_link_search_box, save_memory

def render():
    """
    渲染世界观设定录入模块。
    允许用户通过多维卡片录入角色、势力或世界观概念，并支持双链联想。
    """
    st.header("📝 世界观与角色百科词条录入")
    st.caption("自由构建立体词条：通过多维卡片，将小标题、核心关键词与详细正文挂载！")

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

    st.markdown("#### 🧩 多维特性与模块化卡片")
    session_key = f"cards_{entry_name if entry_name else 'default'}"
    if session_key not in st.session_state:
        st.session_state[session_key] = [{"sub_title": "核心身份与动机", "keywords": "时间回溯, 观测者", "content": ""}]

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
            updated_cards.append({"sub_title": sub_title, "keywords": keywords, "content": content})
            
    st.session_state[session_key] = updated_cards

    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        if st.button("➕ 添加维度", use_container_width=True, disabled=st.session_state.is_generating):
            st.session_state[session_key].append({"sub_title": "", "keywords": "", "content": ""})
            st.rerun()
    with col_btn2:
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
                # 保存到本地记忆库
                save_memory(st.session_state.compiler_memory)
                st.success(f"🎉 包含多维模块的词条【{entry_name}】已成功写入世界观百科库！")
                st.rerun()
            else:
                st.warning("⚠️ 必须填写【词条名称】才能保存！")
