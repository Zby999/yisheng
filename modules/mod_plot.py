import streamlit as st
import sys
import os

# 确保能找到外层的 utils.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_memory

def render():
    """
    渲染智能剧情回溯与自动归档中心模块。
    允许存入原始剧情片段，并提供全局扫描功能以自动关联至角色档案。
    """
    st.header("🤖 智能剧情回溯与自动归档中心")
    if "raw_plot_pool" not in st.session_state.compiler_memory:
        st.session_state.compiler_memory["raw_plot_pool"] = []

    new_plot_text = st.text_area("📋 随时随地粘贴剧情/随笔原文：", height=120, disabled=st.session_state.is_generating)
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("📥 存入剧情池", use_container_width=True, disabled=st.session_state.is_generating):
            if new_plot_text:
                st.session_state.compiler_memory["raw_plot_pool"].append(new_plot_text)
                # 保存到本地记忆库
                save_memory(st.session_state.compiler_memory)
                st.success("🎉 剧情已成功存入公用池！")
                st.rerun()
            else:
                st.warning("请输入内容！")
    with col_p2:
        if st.button("🔄 全局扫描并归档", type="primary", use_container_width=True, disabled=st.session_state.is_generating):
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
            # 扫描归档后也执行保存操作，避免数据丢失
            save_memory(st.session_state.compiler_memory)
            st.success(f"✨ 全局刷新完毕！完成 {match_count} 处自动关联归档！")
