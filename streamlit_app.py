import streamlit as st
import pandas as pd
import re
from panel_generator import generate_candidate_panels, evaluate_candidates_with_llm, recommend_markers_from_inventory

# --- UI Configuration ---
st.set_page_config(page_title="智能流式 Panel 生成器", layout="wide")
st.title("🫠 FlowCyt Panel Assistant")

# --- Global Constants ---
CSV_FILE = "流式抗体库-20250625小鼠.csv"
MAPPING_FILE = "channel_mapping.json"

# --- Helper Functions ---
@st.cache_data
def get_inventory_targets(csv_path):
    """Extracts unique target names from the inventory CSV."""
    try:
        df = pd.read_csv(csv_path)
        # Simple cleaning to get main target names
        targets = set()
        for t in df['Target'].dropna():
            # Remove content in parentheses to get cleaner names for LLM
            clean_name = re.sub(r'\s*\(.*?\)', '', t).strip()
            if clean_name: # Ensure it's not empty after cleaning
                targets.add(clean_name)
        return sorted(list(targets))
    except Exception as e:
        st.error(f"Failed to load inventory: {e}")
        return []

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
    desired_order = ["Marker", "Fluorochrome", "System Code", "Brightness", "Brand", "Catalog Number", "Clone", "Info"]
    final_cols = [col for col in desired_order if col in df.columns]
    st.dataframe(df[final_cols], use_container_width=True, hide_index=True)

# --- Session State Init ---
if "candidates" not in st.session_state:
    st.session_state.candidates = None
if "missing_markers" not in st.session_state:
    st.session_state.missing_markers = []
if "llm_result" not in st.session_state:
    st.session_state.llm_result = None
if "show_all" not in st.session_state:
    st.session_state.show_all = False
if "current_markers" not in st.session_state:
    st.session_state.current_markers = "CD45.2, CD3, NK1.1, Perforin, Granzyme B, TNF-α, IFN-γ"


# --- Load Data ---
available_targets = get_inventory_targets(CSV_FILE)

# --- Main Layout ---
tab1, tab2 = st.tabs(["🧠 AI 实验设计 (Exp. Design)", "🛠️ Panel 生成 (Panel Gen)"])

# ==========================================
# TAB 1: AI Experimental Design
# ==========================================
with tab1:
    st.header("AI 实验助手")
    st.markdown("描述您的实验目的，AI 将基于**现有库存**为您推荐最佳 Marker 组合。")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        exp_goal = st.text_area("实验目的 (Experimental Goal):", "研究肿瘤微环境中 CD8 T 细胞的耗竭状态 (Exhaustion) ...")
    with col2:
        num_colors = st.number_input("期望颜色数 (Target Colors):", min_value=1, max_value=30, value=8)

    if st.button("🤖 推荐 Markers (Recommend)", type="primary"):
        with st.spinner("正在分析库存并构建实验方案..."):
            rec_result = recommend_markers_from_inventory(exp_goal, num_colors, available_targets)
        
        if rec_result["status"] == "error":
            st.error(f"推荐失败: {rec_result['message']}")
        else:
            st.success("推荐方案已生成！")
            rec_markers = rec_result["selected_markers"]
            details = rec_result.get("markers_detail", [])
            
            st.markdown(f"### 推荐列表 ({len(rec_markers)} Markers)")
            st.code(", ".join(rec_markers), language="text")
            
            # Show Rationale Table
            if details:
                st.subheader("💡 设计理由 (Design Rationale)")
                df_details = pd.DataFrame(details)
                # Rename for display if keys match default prompt output
                df_details.rename(columns={
                    "marker": "靶标 (Marker)", 
                    "type": "类型 (Type)", 
                    "reason": "概述 (Rationale)"
                }, inplace=True)
                
                # Ensure column order
                cols = ["靶标 (Marker)", "类型 (Type)", "概述 (Rationale)"]
                final_cols = [c for c in cols if c in df_details.columns]
                
                st.dataframe(df_details[final_cols], use_container_width=True, hide_index=True)
            
            # Action to transfer to Tab 2
            if st.button("✅ 采用此方案 (Use This Panel)"):
                st.session_state.current_markers = ", ".join(rec_markers)
                st.info("Marker 列表已更新。请手动切换到 **'Panel 生成'** 标签页，输入框中已预填充，您可以直接搜索或复制使用。")

# ==========================================
# TAB 2: Panel Generation (Manual/Auto)
# ==========================================
with tab2:
    st.header("Panel 生成器")
    
    # Input Section
    user_markers_input = st.text_input(
        "输入目标 Markers (用逗号分隔):",
        value=st.session_state.current_markers,
        key="marker_input_box"
    )
    
    # Sync back to session state if user manually types
    if user_markers_input != st.session_state.current_markers:
        st.session_state.current_markers = user_markers_input

    if st.button("🔍 搜索可行 Panel (Search Panels)", type="primary"):
        # Reset state
        st.session_state.candidates = None
        st.session_state.llm_result = None
        st.session_state.show_all = False
        
        if not user_markers_input:
            st.warning("请先输入 Markers。")
        else:
            user_markers = [m.strip() for m in user_markers_input.split(',') if m.strip()]

            with st.spinner("正在搜索无冲突组合..."):
                result = generate_candidate_panels(user_markers, CSV_FILE, MAPPING_FILE, max_solutions=10)
            
            if result["status"] == "error":
                st.error(result["message"])
            else:
                st.session_state.candidates = result["candidates"]
                st.session_state.missing_markers = result["missing_markers"]
                if st.session_state.missing_markers:
                    st.warning(f"以下 Marker 未在库存中找到: {', '.join(st.session_state.missing_markers)}")
                st.success(f"成功找到 {len(result['candidates'])} 个无冲突方案！")

    # Results Display
    if st.session_state.candidates:
        candidates = st.session_state.candidates
        limit = 3 if not st.session_state.show_all else len(candidates)
        display_candidates = candidates[:limit]

        st.subheader("📋 候选方案预览 (Candidate Panels)")
        
        display_tabs = st.tabs([f"Option {i+1}" for i in range(len(display_candidates))])
        for i, tab in enumerate(display_tabs):
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
        st.markdown("让 AI 协助您从上述所有方案中选择最佳的一个，并生成圈门策略。")
        
        if st.button("✨ 开始 AI 评估 (Evaluate All Options)"):
            # Evaluate all candidates
            
            with st.spinner(f"AI 正在分析 {len(candidates)} 个方案的亮度匹配与光谱干扰..."):
                ai_result = evaluate_candidates_with_llm(candidates, st.session_state.missing_markers)
            
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
                    gating_detail = res.get("gating_detail", [])
                    if gating_detail:
                        df_gating = pd.DataFrame(gating_detail)
                        # Rename cols
                        df_gating.rename(columns={
                            "step": "步骤",
                            "parent": "上级门 (Parent Gate)",
                            "axis": "X轴/Y轴 (Axes)",
                            "gate": "圈门操作 (Gating)",
                            "population": "含义 (Population)"
                        }, inplace=True)
                        
                        # Ensure order
                        g_cols = ["步骤", "上级门 (Parent Gate)", "X轴/Y轴 (Axes)", "圈门操作 (Gating)", "含义 (Population)"]
                        final_g_cols = [c for c in g_cols if c in df_gating.columns]
                        
                        st.dataframe(df_gating[final_g_cols], use_container_width=True, hide_index=True)
                    else:
                        # Fallback for old text format
                        st.markdown(res.get("gating_strategy", "暂无策略"))