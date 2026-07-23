import streamlit as st
import pandas as pd
from analysis.charts import score_radar
from config import GRADE_ORDER, PATH_NAMES


def render_enterprise_query(df):
    st.header("企业查询")

    if "企业名称" not in df.columns:
        st.warning("数据中未找到企业名称列，无法进行企业查询")
        return

    search_mode = st.radio("查询方式", ["关键词搜索", "条件筛选"], horizontal=True, key="ent_mode")

    if search_mode == "关键词搜索":
        _keyword_search(df)
    else:
        _condition_filter(df)


def _keyword_search(df):
    query = st.text_input("  输入企业名称关键词", placeholder="如：沧州、机械、渔具、六哥...", key="ent_search")
    if query:
        mask = df["企业名称"].astype(str).str.contains(query, case=False, na=False)
        results = df[mask]
        st.info(f"找到 {len(results)} 家匹配企业")
        if len(results) > 0:
            show_cols = [c for c in ["企业名称", "等级", "路径", "总分", "所属地区", "产业集群", "主营产品类别", "联系人", "联系电话"] if c in results.columns]
            st.dataframe(results[show_cols], use_container_width=True, height=min(400, 35 * len(results) + 40))
            _show_enterprise_list(df, results)


def _condition_filter(df):
    col1, col2 = st.columns(2)
    with col1:
        if "等级" in df.columns:
            grades = st.multiselect("等级", GRADE_ORDER, key="ent_grade")
        else:
            grades = []
    with col2:
        if "路径" in df.columns:
            all_paths = sorted(df["路径"].dropna().unique())
            paths = st.multiselect("路径", all_paths, key="ent_path")
        else:
            paths = []

    score_range = None
    if "总分" in df.columns and df["总分"].notna().any():
        smin = float(df["总分"].min())
        smax = float(df["总分"].max())
        score_range = st.slider(
            "总分区间",
            min_value=smin,
            max_value=smax,
            value=(smin, smax),
            key="ent_score",
        )

    if "所属地区" in df.columns:
        regions = sorted(df["所属地区"].dropna().unique())
        sel_regions = st.multiselect("所属地区", regions, key="ent_region")
    else:
        sel_regions = []

    filtered = df.copy()
    if grades:
        filtered = filtered[filtered["等级"].isin(grades)]
    if paths:
        filtered = filtered[filtered["路径"].isin(paths)]
    if score_range:
        filtered = filtered[(filtered["总分"] >= score_range[0]) & (filtered["总分"] <= score_range[1])]
    if sel_regions:
        filtered = filtered[filtered["所属地区"].isin(sel_regions)]

    st.info(f"筛选结果: {len(filtered)} 家企业")
    if len(filtered) > 0:
        _show_enterprise_list(df, filtered)


def _show_enterprise_list(df_all, results):
    if "企业名称" in results.columns:
        names = results["企业名称"].tolist()
        selected = st.selectbox("选择企业查看详情", names, key="ent_select")

        if selected:
            row = df_all[df_all["企业名称"] == selected].iloc[0]
            _show_enterprise_card(row, df_all)


def _show_enterprise_card(row, df_all):
    name = row.get("企业名称", "未知")
    grade = row.get("等级", "N/A")
    path = row.get("路径", "N/A")
    total = row.get("总分", None)

    st.markdown("---")
    st.subheader(f"  {name}")

    c1, c2, c3 = st.columns(3)
    c1.metric("等级", grade)
    c2.metric("路径", f"{path} ({PATH_NAMES.get(str(path), '')})" if pd.notna(path) else "未分配")
    c3.metric("总分", f"{total:.1f}" if pd.notna(total) else "N/A")

    score_cols = {
        "外贸基础能力": ("外贸基础能力", 25),
        "电商运营能力": ("电商运营能力", 23),
        "合作配合意愿": ("合作配合意愿", 35),
        "产能承接配套": ("产能承接配套", 17),
    }

    scores = {}
    for col, (label, max_val) in score_cols.items():
        val = row.get(col, None)
        if pd.notna(val):
            scores[label] = float(val)

    if scores:
        fig = score_radar(df_all, scores)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        cols = st.columns(len(scores))
        for i, (label, val) in enumerate(scores.items()):
            max_val = score_cols[label][1]
            pct = val / max_val * 100
            cols[i].metric(label, f"{val:.0f}/{max_val}", f"{pct:.0f}%")

    with st.expander("  查看全部字段信息", expanded=True):
        skip_cols = {"企业名称", "等级", "路径", "总分", "等级_排序",
                     "外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套"}
        info_items = []
        for col in row.index:
            if col not in skip_cols and pd.notna(row[col]) and str(row[col]).strip() not in ["", "nan"]:
                info_items.append((col, row[col]))
        if info_items:
            ic1, ic2 = st.columns(2)
            for i, (label, val) in enumerate(info_items):
                [ic1, ic2][i % 2].write(f"**{label}**: {val}")
        else:
            st.write("无额外信息")

    _show_ranking(row, df_all)


def _show_ranking(row, df_all):
    if "总分" not in df_all.columns or pd.isna(row.get("总分")):
        return

    with st.expander("排名信息"):
        score = row["总分"]
        total_rank = (df_all["总分"] > score).sum() + 1
        total_count = df_all["总分"].notna().sum()
        st.write(f"**总分排名**: {total_rank}/{total_count}")

        grade = row.get("等级")
        if pd.notna(grade) and "等级" in df_all.columns:
            grade_df = df_all[df_all["等级"] == grade]
            if len(grade_df) > 1:
                grade_rank = (grade_df["总分"] > score).sum() + 1
                st.write(f"**同等级排名**: {grade_rank}/{len(grade_df)} ({grade})")

        path = row.get("路径")
        if pd.notna(path) and "路径" in df_all.columns:
            path_df = df_all[df_all["路径"] == path]
            if len(path_df) > 1:
                path_rank = (path_df["总分"] > score).sum() + 1
                st.write(f"**同路径排名**: {path_rank}/{len(path_df)} (路径={path})")

        score_dims = ["外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套"]
        for dim in score_dims:
            if dim in df_all.columns and pd.notna(row.get(dim)):
                dim_rank = (df_all[dim] > row[dim]).sum() + 1
                dim_total = df_all[dim].notna().sum()
                st.write(f"**{dim}排名**: {dim_rank}/{dim_total}")
