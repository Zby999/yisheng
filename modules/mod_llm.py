import streamlit as st
import requests
import json

def render(api_choice, api_key, ollama_model, gguf_path):
    """
    渲染大模型推演生成中心模块。
    根据不同的模型连接方式执行推演逻辑，提供参数调节功能并进行结果存留展示。
    """
    st.header("⚖️ 大模型推演生成中心")
    
    user_input = st.text_area(
        "✍️ 玩家/读者最新输入剧情：",
        "我掏出枪，试图砸毁这台晶体管计算机，强行终止死亡回溯！", 
        height=100,
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
        generate_only = st.button("👁️ 仅生成提示词", use_container_width=True, disabled=st.session_state.is_generating)
    with btn_col2:
        send_api = st.button("⚡ 编译并发送推演", type="primary", use_container_width=True, disabled=st.session_state.is_generating)

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
            
            st.code(final_prompt, language="markdown")

            if send_api:
                st.session_state.is_generating = True
                st.subheader("🎬 大模型推演结果：")
                
                if api_choice == "🦙 Ollama 本地托管服务":
                    with st.spinner("Ollama 正在运算中..."):
                        try:
                            response = requests.post(
                                "http://localhost:11434/api/generate",
                                json={"model": ollama_model, "prompt": final_prompt, "stream": True, "options": {"num_predict": 2048, "temperature": 0.7}},
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
                                        if body.get("done", False): break
                                output_placeholder.markdown(full_response)
                                st.session_state.history_outputs.append({"input": user_input, "output": full_response})
                                st.success("🎉 推演结果已归档！")
                            else:
                                st.error(f"调用失败，状态码: {response.status_code}")
                        except Exception as e:
                            st.error(f"连接 Ollama 失败: {e}")
                        finally:
                            st.session_state.is_generating = False
                            st.rerun()

                elif api_choice == "📁 本地绝对地址直接加载 (GGUF)":
                    with st.spinner("正在加载本地模型权重..."):
                        try:
                            from llama_cpp import Llama
                            @st.cache_resource
                            def load_local_model(path):
                                return Llama(model_path=path, n_ctx=2048, verbose=False)
                            llm = load_local_model(gguf_path)
                            output = llm(final_prompt, max_tokens=2048, temperature=0.7, stream=True)
                            full_response = ""
                            output_placeholder = st.empty()
                            for chunk in output:
                                delta = chunk["choices"][0]["text"]
                                full_response += delta
                                output_placeholder.markdown(full_response + "▌")
                            output_placeholder.markdown(full_response)
                            st.session_state.history_outputs.append({"input": user_input, "output": full_response})
                            st.success("🎉 本地绝对路径模型推演完成！")
                        except ImportError:
                            st.error("❌ 未检测到 `llama_cpp` 库！")
                        except Exception as e:
                            st.error(f"运行出错: {e}")
                        finally:
                            st.session_state.is_generating = False
                            st.rerun()

                elif api_choice == "☁️ 云端 API (DeepSeek)":
                    if not api_key:
                        st.error("❌ 请输入 API Key！")
                        st.session_state.is_generating = False
                    else:
                        with st.spinner("呼叫云端服务器..."):
                            try:
                                response = requests.post(
                                    "https://api.deepseek.com/chat/completions",
                                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                                    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": final_prompt}], "stream": False}
                                )
                                if response.status_code == 200:
                                    res_text = response.json()["choices"][0]["message"]["content"]
                                    st.session_state.history_outputs.append({"input": user_input, "output": res_text})
                                    st.success("🎉 云端推演结果已归档！")
                                else:
                                    st.error(f"API 调用失败: {response.text}")
                            except Exception as e:
                                st.error(f"网络连接出错: {e}")
                            finally:
                                st.session_state.is_generating = False
                                st.rerun()
