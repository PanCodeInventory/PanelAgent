import streamlit as st
import pandas as pd
from panel_generator import generate_candidate_panels, evaluate_candidates_with_llm

# --- UI Configuration ---
st.set_page_config(page_title="智能流式 Panel 生成器", layout="wide")
st.title("🫠 FlowCyt Panel Assistant")

# --- Session State Init ---
if "candidates" not in st.session_state:
    st.session_state.candidates = None
if "missing_markers" not in st.session_state:
    st.session_state.missing_markers = []
if "llm_result" not in st.session_state:
    st.session_state.llm_result = None
if "show_all" not in st.session_state:
    st.session_state.show_all = False

def display_panel_table(panel_dict):
    """Helper to render a single panel as a dataframe."""
    table_data = []
    for marker, info in panel_dict.items():
        row = {"Marker": marker}
        if "Note" in info:
            row["Info"] = info["Note"]
        else:
            row["Fluorochrome"] = info.get("fluorochrome", "-")
            row["System Code"] = info.get("system_code", "-")
            row["Brightness"] = info.get("brightness", "-")
            row["Brand"] = info.get("brand", "-")
            row["Catalog Number"] = info.get("catalog_number", "-")
            row["Clone"] = info.get("clone", "-")
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Define desired column order
    desired_order = ["Marker", "Fluorochrome", "System Code", "Brightness", "Brand", "Catalog Number", "Clone", "Info"]
    
    # Filter columns that actually exist in the dataframe
    final_cols = [col for col in desired_order if col in df.columns]
    
    st.dataframe(df[final_cols], use_container_width=True, hide_index=True)

# --- Input Section ---
st.sidebar.header("Configuration")
user_markers_input = st.text_input(
    "输入目标 Markers (用逗号分隔):",
    "CD45.2, CD3, NK1.1, Perforin, Granzyme B, TNF-α, IFN-γ"
)

if st.button("🔍 搜索可行 Panel (Search Panels)", type="primary"):
    # Reset state
    st.session_state.candidates = None
    st.session_state.llm_result = None
    st.session_state.show_all = False
    
    if not user_markers_input:
        st.warning("请先输入 Markers。")
    else:
        user_markers = [m.strip() for m in user_markers_input.split(',') if m.strip()]
        CSV_FILE = "流式抗体库-20250625小鼠.csv"
        MAPPING_FILE = "channel_mapping.json"

        with st.spinner("正在搜索无冲突组合..."):
            result = generate_candidate_panels(user_markers, CSV_FILE, MAPPING_FILE, max_solutions=10)
        
        if result["status"] == "error":
            st.error(result["message"])
        else:
            st.session_state.candidates = result["candidates"]
            st.session_state.missing_markers = result["missing_markers"]
            if result["missing_markers"]:
                st.warning(f"以下 Marker 未在库存中找到: {', '.join(result['missing_markers'])}")
            st.success(f"成功找到 {len(result['candidates'])} 个无冲突方案！")

# --- Results Display ---
if st.session_state.candidates:
    candidates = st.session_state.candidates
    limit = 3 if not st.session_state.show_all else len(candidates)
    display_candidates = candidates[:limit]

    st.subheader("📋 候选方案预览 (Candidate Panels)")
    
    tabs = st.tabs([f"Option {i+1}" for i in range(len(display_candidates))])
    for i, tab in enumerate(tabs):
        with tab:
            display_panel_table(display_candidates[i])

    # "Show All" Button
    if len(candidates) > 3 and not st.session_state.show_all:
        if st.button(f"👀 查看剩余 {len(candidates)-3} 个方案"):
            st.session_state.show_all = True
            st.rerun()

    st.divider()

    # --- AI Expert Section ---
    st.subheader("🤖 AI 专家评估 (Expert Evaluation)")
    st.markdown("让 AI 协助您从上述前 3 个方案中选择最佳的一个，并生成圈门策略。")
    
    if st.button("✨ 开始 AI 评估 (Evaluate Top 3 Options)"):
        # Take top 3 for evaluation to save tokens
        top_candidates = candidates[:3]
        
        with st.spinner("AI 正在分析亮度匹配与光谱干扰..."):
            ai_result = evaluate_candidates_with_llm(top_candidates, st.session_state.missing_markers)
        
        st.session_state.llm_result = ai_result
    
    # Display AI Result
    if st.session_state.llm_result:
        res = st.session_state.llm_result
        if res["status"] == "error":
            st.error(f"AI 评估失败: {res['message']}")
        else:
            st.success("AI 评估完成！")
            
            st.markdown("### 🏆 推荐方案 (Best Option)")
            display_panel_table(res["selected_panel"])
            
            st.info(f"**💡 推荐理由:**\n\n{res['rationale']}")
            
            with st.expander("🚪 查看圈门策略 (Gating Strategy)", expanded=True):
                st.markdown(res["gating_strategy"])


