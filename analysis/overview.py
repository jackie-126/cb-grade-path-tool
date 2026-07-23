import streamlit as st
import pandas as pd
from analysis.charts import (
    grade_pie, grade_bar, path_bar, grade_path_heatmap,
    score_boxplot, score_by_grade_boxplot, score_scatter_matrix,
)
from config import GRADE_ORDER


def render_overview(df):
    st.header("数据总览")

    _render_metric_cards(df)

    col1, col2 = st.columns(2)
    with col1:
        fig = grade_pie(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = path_bar(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    fig = grade_path_heatmap(df)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig = score_boxplot(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col4:
        fig = score_by_grade_boxplot(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("显示评分维度相关性矩阵", key="show_scatter"):
        fig = score_scatter_matrix(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    _render_data_table(df)


def _render_metric_cards(df):
    total = len(df)

    a_count = len(df[df["等级"] == "A级"]) if "等级" in df.columns else 0
    b_count = len(df[df["等级"] == "B级"]) if "等级" in df.columns else 0

    path_count = 0
    if "路径" in df.columns:
        path_count = df["路径"].apply(lambda x: pd.notna(x) and str(x).strip() not in ["", "nan", "无匹配路径"]).sum()

    avg_score = df["总分"].mean() if "总分" in df.columns else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("企业总数", total)
    c2.metric("A级+B级", f"{a_count + b_count} ({(a_count+b_count)/total*100:.1f}%)" if total > 0 else "0")
    c3.metric("有路径企业", f"{path_count} ({path_count/total*100:.1f}%)" if total > 0 else "0")
    c4.metric("平均总分", f"{avg_score:.1f}" if avg_score else "N/A")

    if "等级" in df.columns:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        for i, grade in enumerate(GRADE_ORDER):
            count = len(df[df["等级"] == grade])
            pct = count / total * 100 if total > 0 else 0
            [c1, c2, c3, c4, c5, c6][i].metric(grade, f"{count} ({pct:.1f}%)")


def _render_data_table(df):
    st.subheader("企业明细表")

    search_query = st.text_input("  搜索企业名称", placeholder="输入企业名称关键词...", key="tbl_search")

    filter_cols = []
    if "等级" in df.columns:
        filter_cols.append("等级")
    if "路径" in df.columns:
        filter_cols.append("路径")

    filtered = df.copy()

    if search_query and "企业名称" in filtered.columns:
        mask = filtered["企业名称"].astype(str).str.contains(search_query, case=False, na=False)
        filtered = filtered[mask]

    if filter_cols:
        fcol1, fcol2, fcol3 = st.columns(3)

        with fcol1:
            if "等级" in df.columns:
                grades = st.multiselect("筛选等级", GRADE_ORDER, key="tbl_grade")
                if grades:
                    filtered = filtered[filtered["等级"].isin(grades)]

        with fcol2:
            if "路径" in df.columns:
                all_paths = sorted(df["路径"].dropna().unique())
                paths = st.multiselect("筛选路径", all_paths, key="tbl_path")
                if paths:
                    filtered = filtered[filtered["路径"].isin(paths)]

        with fcol3:
            if "总分" in df.columns and df["总分"].notna().any():
                smin = float(df["总分"].min())
                smax = float(df["总分"].max())
                score_range = st.slider(
                    "总分区间",
                    min_value=smin,
                    max_value=smax,
                    value=(smin, smax),
                    key="tbl_score",
                )
                filtered = filtered[
                    (filtered["总分"] >= score_range[0]) & (filtered["总分"] <= score_range[1])
                ]

    st.caption(f"筛选结果: {len(filtered)} / {len(df)} 家企业")

    st.dataframe(
        filtered.style.background_gradient(subset=["总分"], cmap="RdYlGn") if "总分" in filtered.columns else filtered,
        use_container_width=True,
        height=min(600, 40 * len(filtered) + 40),
    )
