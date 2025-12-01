import streamlit as st
import pandas as pd
from panel_generator import generate_panel_simple

# --- UI Configuration ---
st.set_page_config(page_title="智能流式 Panel 生成器", layout="wide")
st.title("🫠 FlowCyt LLM-Assistant (Simple Mode)")
st.markdown("""
    **极简模式:** 直接基于库存生成无冲突的 Panel。
    请输入 Markers，AI 将尝试为您找到最佳的抗体组合。
""")

# --- Input Section ---
user_markers_input = st.text_input(
    "输入目标 Markers (用逗号分隔):",
    "CD45.2, CD3, NK1.1, Perforin, Granzyme B, TNF-α, IFN-γ"
)

if st.button("生成 Panel", type="primary"):
    if not user_markers_input:
        st.warning("请先输入 Markers。")
    else:
        user_markers = [m.strip() for m in user_markers_input.split(',') if m.strip()]
        
        CSV_FILE = "流式抗体库-20250625小鼠.csv"
        MAPPING_FILE = "channel_mapping.json"

        with st.spinner(f"正在为 {len(user_markers)} 个 Markers 搜索最佳组合..."):
            # Call the new simple generator
            result = generate_panel_simple(user_markers, CSV_FILE, MAPPING_FILE)

        # --- Result Display ---
        if result["status"] == "error":
            st.error(f"发生错误: {result['message']}")
        else:
            st.success("Panel 生成完毕！")
            
            data = result["panel_data"]
            
            # 1. Show Panel Table
            panel_dict = data.get("Panel", {})
            if panel_dict:
                # Convert dict to a nice DataFrame for display
                # We flatten the dict: Key is Marker, Values are columns
                table_data = []
                for marker, info in panel_dict.items():
                    row = {"Marker": marker}
                    if "Note" in info:
                        row["Info"] = info["Note"]
                    else:
                        row["Fluorochrome"] = info.get("fluorochrome", "-")
                        row["Clone"] = info.get("clone", "-")
                        row["Brand"] = info.get("brand", "-") # Added Brand
                        row["Catalog Number"] = info.get("catalog_number", "-") # Added Catalog Number
                    table_data.append(row)
                
                df = pd.DataFrame(table_data)
                # Reorder columns for better presentation
                display_cols = ["Marker", "Fluorochrome", "Clone", "Brand", "Catalog Number", "Info"]
                # Filter out 'Info' if not present in any row
                df = df[[col for col in display_cols if col in df.columns]]
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("结果为空。")

            # 2. Show Rationale
            st.subheader("💡 设计理由")
            st.info(data.get("Design_Rationale", "无"))

