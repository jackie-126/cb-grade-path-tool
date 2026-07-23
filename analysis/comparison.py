import streamlit as st
import pandas as pd
from analysis.charts import comparison_bar, comparison_grade_stacked
from config import GRADE_ORDER


def render_comparison(datasets):
    st.header("跨地区对比")

    if len(datasets) < 2:
        st.info("请在侧边栏上传2个以上文件以进行跨地区对比")
        return

    st.subheader("基础指标对比")
    _show_summary_table(datasets)

    st.subheader("等级分布对比")
    fig = comparison_grade_stacked(datasets)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("平均总分对比")
    fig = comparison_bar(datasets, "总分", "各地区平均总分")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("各维度平均分对比")
    score_dims = ["外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套"]
    for dim in score_dims:
        has_dim = any(dim in df.columns for df in datasets.values())
        if has_dim:
            fig = comparison_bar(datasets, dim, f"各地区平均{dim}")
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    st.subheader("路径分布对比")
    _show_path_comparison(datasets)


def _show_summary_table(datasets):
    rows = []
    for name, df in datasets.items():
        row = {"地区": name, "企业总数": len(df)}

        if "等级" in df.columns:
            for grade in GRADE_ORDER:
                count = len(df[df["等级"] == grade])
                row[f"{grade}数"] = count
                row[f"{grade}占比"] = f"{count/len(df)*100:.1f}%" if len(df) > 0 else "0%"

        if "总分" in df.columns:
            row["平均总分"] = f"{df['总分'].mean():.1f}" if df["总分"].notna().any() else "N/A"

        score_dims = ["外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套"]
        for dim in score_dims:
            if dim in df.columns and df[dim].notna().any():
                row[f"平均{dim}"] = f"{df[dim].mean():.1f}"

        if "路径" in df.columns:
            total_path = df["路径"].apply(lambda x: pd.notna(x) and str(x).strip() not in ["", "nan"]).sum()
            row["有路径数"] = total_path

        rows.append(row)

    summary_df = pd.DataFrame(rows)
    st.dataframe(summary_df, use_container_width=True)


def _show_path_comparison(datasets):
    all_paths = set()
    for df in datasets.values():
        if "路径" in df.columns:
            all_paths.update(df["路径"].dropna().unique())
    all_paths = sorted(all_paths)

    if not all_paths:
        st.info("数据中无路径信息")
        return

    rows = []
    for name, df in datasets.items():
        row = {"地区": name}
        for path in all_paths:
            if "路径" in df.columns:
                count = len(df[df["路径"] == path])
                row[path] = count
            else:
                row[path] = 0
        rows.append(row)

    path_df = pd.DataFrame(rows)
    st.dataframe(path_df, use_container_width=True)

    path_cols = [c for c in path_df.columns if c != "地区"]
    if path_cols:
        import plotly.express as px
        melted = path_df.melt(id_vars="地区", var_name="路径", value_name="数量")
        fig = px.bar(
            melted, x="路径", y="数量", color="地区",
            barmode="group",
            title="各地区路径分布对比",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
