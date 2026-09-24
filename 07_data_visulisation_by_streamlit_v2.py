import streamlit as st
import pandas as pd
import os
from pathlib import Path
from PIL import Image

import importlib.util

spec = importlib.util.spec_from_file_location("overview_mod", Path("071_overview_page.py"))
overview_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overview_mod)
render_overview = overview_mod.render_overview

# 动态导入 072_abnormal_page.py
spec_ab = importlib.util.spec_from_file_location("abnormal_mod", Path("072_abnormal_page.py"))
abnormal_mod = importlib.util.module_from_spec(spec_ab)
spec_ab.loader.exec_module(abnormal_mod)
render_abnormal = abnormal_mod.render_abnormal

DATA_DIRS = {
    "abnormal": "output_abnormal_analytics",
    "further": "output_further_analytics"
}

def scan_dir(base_path):
    base = Path(base_path)
    groups = {}
    for p in base.rglob("*"):
        if p.is_file():
            # group key: first-level subdir or filename prefix before '__' or '_'
            rel = p.relative_to(base)
            if len(rel.parts) > 1:
                key = rel.parts[0]
            else:
                name = p.stem
                key = name.split("__")[0].split("_")[0]
            groups.setdefault(key, []).append(p)
    # sort files per group
    for k in groups:
        groups[k] = sorted(groups[k], key=lambda p: str(p))
    return groups

def render_resource(p):
    ext = p.suffix.lower()
    if ext in [".parquet"]:
        if ext == ".parquet":
            try:
                df = pd.read_parquet(p)
                st.dataframe(df)
            except Exception as e:
                st.error(f"无法读取表格: {e}")
    elif ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        img = Image.open(p)
        st.image(img, use_column_width=True)
    elif ext in [".md", ".txt"]:
        text = p.read_text(encoding="utf-8", errors="replace")
        st.markdown(text)
    elif ext in [".json"]:
        try:
            obj = pd.read_json(p)
            st.dataframe(obj)
        except Exception:
            st.text(p.read_text(encoding="utf-8", errors="replace"))
    else:
        st.write(f"未展示的文件类型: {p.name}")

def main():
    st.title("日志分析 — 概览（overview）")
    st.sidebar.markdown("选择展示：")
    choice = st.sidebar.radio("视图", ["overview", "abnormal"], index=0)

    if choice == "overview":
        render_overview(DATA_DIRS["further"])
        return

    if choice == "abnormal":
        render_abnormal(DATA_DIRS["abnormal"], DATA_DIRS["further"])
        return

    # 原来的 files 分支（保留你现有的实现）
    chosen_dir = st.radio("选择分析类型", ["overview", "abnormal"])
    groups = scan_dir(DATA_DIRS[chosen_dir])

    if not groups:
        st.warning(f"目录 {DATA_DIRS[chosen_dir]} 中未发现资源")
        return

    keys = sorted(groups.keys())
    idx = st.sidebar.number_input("选择故事线索引（页）", min_value=0, max_value=len(keys)-1, value=0)
    selected_key = keys[idx]
    st.sidebar.write(f"共 {len(keys)} 条故事线")
    st.header(f"故事线：{selected_key} ({idx+1}/{len(keys)})")

    for p in groups[selected_key]:
        st.subheader(p.name)
        render_resource(p)

    st.sidebar.selectbox("跳转到故事线", keys, index=idx, format_func=lambda x: f"{x}")

    


if __name__ == "__main__":
    main()