import streamlit as st
import json
import os

# 定义本地记忆库文件名称
MEMORY_FILE = "world_memory.json"

def load_memory():
    """
    读取本地 JSON 记忆库文件。
    如果文件不存在或读取失败，则返回初始化的空字典结构。
    """
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"characters": {}, "factions": {}, "raw_plot_pool": []}
    return {"characters": {}, "factions": {}, "raw_plot_pool": []}

def save_memory(memory_data):
    """
    将当前世界观数据实时写入本地 JSON 文件进行持久化保存。
    确保中文不会出现乱码。
    """
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, ensure_ascii=False, indent=4)

def render_bi_link_search_box(input_label, input_key, help_text=""):
    """
    渲染一个双链悬浮联想搜索框。
    接收输入关键词，从全局记忆库中检索角色、势力及剧情池，并以悬浮气泡框(Popover)展示结果。
    """
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
            with st.popover(f"💡 悬浮查看：检测到 {len(matched_results)} 个相关历史词条", use_container_width=True):
                # 🌟 核心升级 1：添加固定高度的滑动容器（250px），内容超出自动出现滚动条
                with st.container(height=250, border=False):
                    for item_type, title, content_dict in matched_results:
                        
                        # 🌟 核心升级 2：使用 HTML+CSS 进行精细化排版，字号调小至 13px
                        html_str = f"<div style='font-size: 13px; line-height: 1.6;'>"
                        html_str += f"<strong style='font-size: 14px; color: #1f77b4;'>📌 [{item_type}] {title}</strong><br>"
                        
                        for k, v in content_dict.items():
                            if isinstance(v, dict):
                                # 解析多维字典结构，不再直接打印出难看的 {'keywords': ...}
                                html_str += f"<span style='color: #444;'><b>{k}</b>:</span><br>"
                                if 'keywords' in v:
                                    html_str += f"<span style='margin-left: 15px; color: #666;'><i>标签:</i> {', '.join(v['keywords'])}</span><br>"
                                if 'content' in v:
                                    html_str += f"<span style='margin-left: 15px; color: #666;'><i>正文:</i> {v['content']}</span><br>"
                            else:
                                html_str += f"<span style='color: #444;'><b>{k}</b>: {v}</span><br>"
                                
                        html_str += "</div><hr style='margin: 10px 0px; border-color: #f0f2f6;'>"
                        
                        # 渲染 HTML
                        st.markdown(html_str, unsafe_allow_html=True)
        else:
            st.caption("✨ 暂未发现历史关联词条，这将是一个全新的原创双链节点。")
            
    return query_text