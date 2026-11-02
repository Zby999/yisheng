import streamlit as st
import sys
import os

# 确保能找到外层的 utils.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_memory

def render():
    """
    渲染融合了“双链织网筛选”与“悬浮滚动预览”的动态档案库模块。
    词条旁实时显示双链计数，点击可呼出带滚动条的悬浮预览框，并支持细颗粒度编辑。
    """
    st.header("🗄️ 世界观动态档案库与双链织网中心")
    st.caption("集成了组合检索、双链计数徽标及可滚动悬浮预览的综合知识库。")

    memory = st.session_state.compiler_memory
    
    # 收集所有的实体数据
    all_entries = {}
    for cat in ["characters", "factions", "world_concepts"]:
        if cat in memory:
            for name, data in memory[cat].items():
                all_entries[name] = {"category": cat, "data": data}

    if not all_entries:
        st.info("💡 当前档案库为空，请先前往【世界观设定录入】模块添加词条。")
        return

    # ==========================================
    # 第一部分：织网筛选控制面板
    # ==========================================
    with st.container(border=True):
        st.markdown("### 🕸️ 组合条件织网筛选")
        
        with st.form(key="archive_search_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            
            with f_col1:
                cat_filter = st.selectbox(
                    "📂 档案分类筛选", 
                    ["全部", "characters", "factions", "world_concepts"],
                    format_func=lambda x: "🌐 全库展示" if x=="全部" else ("🎭 角色人物" if x=="characters" else ("🏛️ 组织阵营" if x=="factions" else "🌍 世界观概念"))
                )
                
            with f_col2:
                keyword_filter = st.text_input("🔎 名称/文字全文搜索", placeholder="输入名字或任意字句...")
                
            with f_col3:
                # 提取标签供检索
                all_tags_set = set()
                for entry_info in all_entries.values():
                    for sub_title, sub_dict in entry_info["data"].items():
                        if isinstance(sub_dict, dict) and "keywords" in sub_dict:
                            for kw in sub_dict["keywords"]:
                                all_tags_set.add(kw.strip())
                
                tag_filter = st.selectbox("🏷️ 按标签织网过滤", ["全部标签"] + sorted(list(all_tags_set)))

            submitted = st.form_submit_button("🔍 执行织网检索", type="primary", use_container_width=True)

    if "search_triggered" not in st.session_state:
        st.session_state.search_triggered = False
    if submitted:
        st.session_state.search_triggered = True

    # ==========================================
    # 第二部分：执行精准过滤
    # ==========================================
    filtered_entries = {}
    has_filters = (cat_filter != "全部") or (keyword_filter.strip() != "") or (tag_filter != "全部标签")

    if st.session_state.search_triggered and has_filters:
        for name, info in all_entries.items():
            if cat_filter != "全部" and info["category"] != cat_filter:
                continue
                
            match_text = True
            if keyword_filter:
                found_text = keyword_filter in name
                for sub_t, sub_d in info["data"].items():
                    if keyword_filter in sub_t: found_text = True
                    if isinstance(sub_d, dict):
                        if keyword_filter in sub_d.get("content", ""): found_text = True
                        if any(keyword_filter in kw for kw in sub_d.get("keywords", [])): found_text = True
                    elif keyword_filter in str(sub_d):
                        found_text = True
                match_text = found_text
            if not match_text:
                continue

            match_tag = True
            if tag_filter != "全部标签":
                has_tag = False
                for sub_t, sub_d in info["data"].items():
                    if isinstance(sub_d, dict) and "keywords" in sub_d:
                        if any(tag_filter in kw for kw in sub_d["keywords"]):
                            has_tag = True
                match_tag = has_tag
            if not match_tag:
                continue
                
            filtered_entries[name] = info

    if not st.session_state.search_triggered or not has_filters:
        st.info("💡 **当前保持清爽留空**：请在上方设置筛选条件并点击【执行织网检索】来精准调取设定。")
    else:
        st.markdown(f"📌 **检索结果：** 找到 **{len(filtered_entries)}** 个匹配词条")
    st.markdown("---")

    # ==========================================
    # 第三部分：带“双链计数徽标”与“滚动悬浮框”的卡片展示
    # ==========================================
    for name, info in filtered_entries.items():
        cat = info["category"]
        cat_badge = "🎭 角色" if cat=="characters" else ("🏛️ 势力" if cat=="factions" else "🌍 概念")
        
        # 1. 自动计算该词条的双链关联数（全局扫描名字、标签、或正文中有提及该名字的其他地方/剧情切片）
        bi_links = []
        # 检索其他词条中是否包含了当前名字
        for other_name, other_info in all_entries.items():
            if other_name == name: continue
            for st_t, st_d in other_info["data"].items():
                if isinstance(st_d, dict) and (name in st_d.get("content", "") or name in other_name):
                    bi_links.append(("关联词条", other_name, st_t))
        # 检索剧情切片中是否包含了当前名字
        for idx, plot in enumerate(memory.get("raw_plot_pool", [])):
            if name in plot or any(name in str(sub_v.get("keywords", "")) for sub_v in info["data"].values()):
                # 简单双向关联：如果剧情里有这个名字，或者角色标签被剧情命中
                if name in plot:
                    bi_links.append(("剧情切片", f"片段 #{idx+1}", {"原文内容": plot}))

        link_count = len(bi_links)

        # 2. 渲染微型折叠卡片外壳
        with st.expander(f"{cat_badge} ｜ {name}"):
            
            # 顶部操作栏：既有基础信息，又有你要求的双链悬浮按钮
            col_info, col_pop = st.columns([2, 1])
            with col_info:
                st.markdown(
                    f"""<div style='font-size: 13px; color: #555;'>
                    分类：<b>{cat_badge}</b> ｜ 维度数：<b>{len(info['data']) if isinstance(info['data'], dict) else 1}</b>
                    </div>""", 
                    unsafe_allow_html=True
                )
            with col_pop:
                # 🌟 核心亮点：名字旁边的双链计数悬浮按钮 (Popover)
                with st.popover(f"🔗 双链联想 ({link_count})", use_container_width=True):
                    st.markdown(f"**📌 【{name}】的双链知识网络**")
                    # 添加内部固定高度的滚动容器
                    with st.container(height=220, border=False):
                        if bi_links:
                            for item_type, title, content_val in bi_links:
                                html_box = f"<div style='font-size: 12px; line-height: 1.5; margin-bottom: 8px;'>"
                                html_box += f"<b style='color: #1f77b4;'>[{item_type}] {title}</b><br>"
                                if isinstance(content_val, dict):
                                    html_box += f"<span style='color: #666;'>{content_val.get('原文内容', '')}</span>"
                                else:
                                    html_box += f"<span style='color: #666;'>子模块: {content_val}</span>"
                                html_box += "</div><hr style='margin: 4px 0px; border-color: #eee;'>"
                                st.markdown(html_box, unsafe_allow_html=True)
                        else:
                            st.caption("✨ 暂未在其他词条或剧情池中检测到强双链关联。")

            st.markdown("---")

            # 3. 细颗粒度子模块编辑区
            entry_data = info["data"]
            updated_sub_modules = {}
            
            if isinstance(entry_data, dict):
                sub_keys = list(entry_data.keys())
                
                for idx, sub_title_old in enumerate(sub_keys):
                    sub_dict = entry_data[sub_title_old]
                    
                    with st.container(border=True):
                        st.markdown(f"<span style='font-size: 13px; font-weight: bold;'>🔹 子模块: {sub_title_old}</span>", unsafe_allow_html=True)
                        
                        if isinstance(sub_dict, dict):
                            current_kw = ", ".join(sub_dict.get("keywords", []))
                            current_cnt = sub_dict.get("content", "")
                        else:
                            current_kw = ""
                            current_cnt = str(sub_dict)

                        col_e1, col_e2 = st.columns([1, 1])
                        with col_e1:
                            new_sub_title = st.text_input("修改子模块标题", value=sub_title_old, key=f"edit_title_{name}_{idx}")
                        with col_e2:
                            new_keywords = st.text_input("修改标签 (逗号分隔)", value=current_kw, key=f"edit_kw_{name}_{idx}")
                            
                        new_content = st.text_area("修改详细正文说明", value=current_cnt, key=f"edit_cnt_{name}_{idx}", height=75)
                        
                        col_sub_del, col_space = st.columns([1, 4])
                        with col_sub_del:
                            if st.button(f"🗑️ 仅删除此模块", key=f"del_sub_{name}_{sub_title_old}_{idx}"):
                                del entry_data[sub_title_old]
                                save_memory(memory)
                                st.success(f"已从【{name}】中删除了子模块【{sub_title_old}】！")
                                st.rerun()

                        if new_sub_title:
                            updated_sub_modules[new_sub_title] = {
                                "keywords": [kw.strip() for kw in new_keywords.split(",") if kw.strip()],
                                "content": new_content
                            }
                
                memory[cat][name] = updated_sub_modules

            # 4. 底部整体操作栏
            st.markdown("")
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button(f"💾 保存对【{name}】的修改", key=f"save_entry_{name}", type="primary", use_container_width=True):
                    save_memory(memory)
                    st.success(f"🎉 词条【{name}】更新成功并已写入本地硬盘！")
                    st.rerun()
            with col_act2:
                if st.button(f"🔥 彻底删除整条档案 [{name}]", key=f"del_entire_{name}", use_container_width=True):
                    del memory[cat][name]
                    save_memory(memory)
                    st.success(f"已彻底删除档案【{name}】！")
                    st.rerun()