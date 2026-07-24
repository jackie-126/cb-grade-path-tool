import streamlit as st
import pandas as pd
from core.data_loader import handle_file_upload
from core.questionnaire_detector import detect_questionnaire_columns, compute_scores_for_dataframe, get_detection_summary_questionnaire, classify_stage
from core.path_calculator import detect_path_columns, compute_paths_for_dataframe, get_detection_summary_path

FIELD_LABELS_PATH = {
    "enterprise_name": "企业名称", "direction_intent": "方向意图",
    "customer_profile": "客户画像", "product_category": "主营产品",
    "sku_count": "SKU数量", "moq": "最小起订量",
    "has_rd_team": "研发团队", "has_product_images": "高清产品图",
    "is_core_supplier": "核心供应商",
}
from analysis.overview import render_overview
from analysis.enterprise import render_enterprise_query
from analysis.comparison import render_comparison
from export.report_generator import generate_report
from utils.scoring_rules import get_score_breakdown, get_grade_thresholds
from utils.path_rules import explain_path

st.set_page_config(page_title="跨境电商智能分析Agent", page_icon=" ", layout="wide", initial_sidebar_state="expanded")

st.title("  跨境电商智能分析Agent")


with st.sidebar:
    st.header("  选择模式")
    mode = st.radio(
        "功能模式",
        ["计算得分和等级", "划分路径", "得分等级+路径", "已有得分等级和路径"],
        index=3,
        help="根据你的数据情况选择对应模式",
    )
    st.divider()

    st.header("  数据导入")
    uploaded_files = st.file_uploader("上传Excel/CSV文件（支持多文件对比）", type=["xlsx", "xls", "csv"], accept_multiple_files=True)

    st.divider()
    if mode in ["计算得分和等级", "得分等级+路径"]:
        st.header("  评分规则参考")
        with st.expander("查看评分标准"):
            st.text(get_score_breakdown())
        with st.expander("查看等级划分"):
            st.text(get_grade_thresholds())

    if mode in ["划分路径", "得分等级+路径"]:
        st.header("  路径规则参考")
        with st.expander("查看路径划分规则"):
            st.markdown("""
**主干路径判断：**
1. 学习了解/暂不考虑 → **F**
2. 客户含工程/机构 → **E**
3. B2C平台 → **A** | B2B → **B**
4. 给卖家供货 → **C** | 独立站/小B → **D**

**细分：** A1精品/A2铺货 | B1现货/B2定制 | C1代发/C2配送 | D1直播/D2图文 | E1招投标/E2认证 | F1学习/F2缺意愿
            """)

if not uploaded_files:
    st.info("  请在左侧选择模式并上传Excel文件")
    st.markdown("---")
    st.markdown(f"""
### 当前模式: **{mode}**

{"上传包含原始问卷数据的Excel，系统自动计算各维度得分和等级(A-F)" if mode == "计算得分和等级" else ""}
{"上传包含方向意图、客户画像等字段的Excel，系统自动划分出海路径。可上传2个文件，系统自动从第一阶段补齐研发团队等缺失列" if mode == "划分路径" else ""}
{"上传原始问卷数据，系统同时计算得分等级+划分出海路径。可上传2个文件（第一阶段+第二阶段），系统自动按企业名合并" if mode == "得分等级+路径" else ""}
{"上传已有得分和等级的Excel，直接进行数据分析、可视化、生成报告" if mode == "已有得分等级和路径" else ""}

### 支持的文件格式
- 一个地区一个文件，多文件可横向对比
- 不同文件格式可以不同，系统智能识别关键列
    """)
    st.stop()


def process_single_file(uploaded_file, mode, file_key="main"):
    with st.spinner(f"正在加载 {uploaded_file.name}..."):
        df = handle_file_upload(uploaded_file, file_key, mode)
    if df is None:
        return None

    if mode == "已有得分等级和路径":
        return df

    used_cols = set()
    used_cols.add("企业名称")

    if mode in ["计算得分和等级", "得分等级+路径"]:
        st.subheader("  评分字段识别")
        q_mapping, q_extra = detect_questionnaire_columns(df)
        st.text(get_detection_summary_questionnaire(df, q_mapping, q_extra))
        enterprise_col = q_mapping.get("enterprise_name")

        with st.expander("手动修正评分字段映射", expanded=False):
            col_options = ["(不识别)"] + list(df.columns)
            new_q_mapping = {}
            field_labels = {
                "enterprise_name": "企业名称", "has_export_experience": "外贸出口经验",
                "is_specialized_enterprise": "专精特新", "is_industry_representative": "产业带代表性",
                "has_innovative_product": "创新产品", "has_exhibition_experience": "展会参展",
                "export_amount": "上年度出口额", "has_ecommerce_experience": "电商供货经验",
                "has_ecommerce_team": "专属电商团队", "ecommerce_platform_count": "平台店铺数量",
                "willing_showroom": "展厅展示", "willing_small_batch": "小批量订单",
                "willing_training_count": "培训人数", "willing_product_materials": "产品素材参数",
                "liaison_count": "对接人数", "capacity_reservation_ratio": "产能预留比例",
                "ecommerce_sales_amount": "电商销售额",
            }
            for field_key, col_name in q_mapping.items():
                label = field_labels.get(field_key, field_key)
                idx = col_options.index(col_name) if col_name in col_options else 0
                sel = st.selectbox(label, col_options, index=idx, key=f"qmap_{file_key}_{field_key}")
                if sel != "(不识别)":
                    new_q_mapping[field_key] = sel
            if st.button("应用修正", key=f"qapply_{file_key}"):
                q_mapping = new_q_mapping

        used_cols.update(q_mapping.values())

        score_df = compute_scores_for_dataframe(df, q_mapping)
        st.success(f"计算完成！共 {len(score_df)} 家企业")

        add_cols = [c for c in ["外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套", "总分", "等级"] if c in score_df.columns]
        name_col = enterprise_col or "企业名称"
        result = df[[c for c in used_cols if c in df.columns]].copy()
        if enterprise_col and enterprise_col in df.columns:
            result = result.merge(score_df[["企业名称"] + add_cols], left_on=enterprise_col, right_on="企业名称", how="left")
            if "企业名称" in result.columns and enterprise_col != "企业名称":
                result.drop(columns=["企业名称"], inplace=True)
            elif enterprise_col != "企业名称" and name_col in result.columns:
                pass
        else:
            for col in add_cols:
                result[col] = score_df[col].values[:len(result)]

        if name_col in result.columns and name_col != "企业名称":
            result.insert(0, "企业名称", result.pop(name_col))
        elif "企业名称" in result.columns:
            result.insert(0, "企业名称", result.pop("企业名称"))

        with st.expander("查看计算结果预览"):
            preview_cols = [c for c in ["企业名称", "总分", "等级", "外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套"] if c in result.columns]
            st.dataframe(result[preview_cols].head(10), use_container_width=True)

        st.download_button(
            "  下载得分等级结果",
            data=result.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_得分等级.csv",
            mime="text/csv",
        )

    if mode in ["划分路径", "得分等级+路径"]:
        st.subheader("  路径字段识别")
        p_mapping, p_extra = detect_path_columns(df)
        st.text(get_detection_summary_path(df, p_mapping, p_extra))
        if not enterprise_col:
            enterprise_col = p_mapping.get("enterprise_name")

        with st.expander("手动修正路径字段映射", expanded=False):
            col_options = ["(不识别)"] + list(df.columns)
            new_p_mapping = {}
            p_labels = {
                "enterprise_name": "企业名称", "direction_intent": "方向意图",
                "customer_profile": "客户画像", "product_category": "主营产品",
                "sku_count": "SKU数量", "moq": "最小起订量",
                "has_rd_team": "研发团队", "has_product_images": "高清产品图",
                "has_product_params": "产品参数表", "is_core_supplier": "核心供应商",
            }
            for field_key, col_name in p_mapping.items():
                label = p_labels.get(field_key, field_key)
                idx = col_options.index(col_name) if col_name in col_options else 0
                sel = st.selectbox(label, col_options, index=idx, key=f"pmap_{file_key}_{field_key}")
                if sel != "(不识别)":
                    new_p_mapping[field_key] = sel
            if st.button("应用修正", key=f"papply_{file_key}"):
                p_mapping = new_p_mapping

        used_cols.update(p_mapping.values())

        path_df = compute_paths_for_dataframe(df, p_mapping)
        st.success(f"路径划分完成！共 {len(path_df)} 家企业")

        if mode == "划分路径":
            result = df[[c for c in used_cols if c in df.columns]].copy()
        add_cols = [c for c in ["主干路径", "出海路径"] if c in path_df.columns]
        if enterprise_col and enterprise_col in df.columns:
            result = result.merge(path_df[["企业名称"] + add_cols], left_on=enterprise_col, right_on="企业名称", how="left")
            if "企业名称" in result.columns and enterprise_col != "企业名称":
                result.drop(columns=["企业名称"], inplace=True)
        else:
            for col in add_cols:
                result[col] = path_df[col].values[:len(result)]

        name_col = enterprise_col or "企业名称"
        if name_col in result.columns and name_col != "企业名称":
            result.insert(0, "企业名称", result.pop(name_col))
        elif "企业名称" in result.columns:
            result.insert(0, "企业名称", result.pop("企业名称"))

        with st.expander("查看路径划分结果预览"):
            st.dataframe(result.head(10), use_container_width=True)

        if mode == "划分路径":
            st.download_button(
                "  下载路径结果",
                data=result.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_路径.csv",
                mime="text/csv",
            )
        else:
            st.download_button(
                "  下载完整结果（得分+等级+路径）",
                data=result.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_完整结果.csv",
                mime="text/csv",
            )

    return result


def process_path_with_supplement(files, file_key="path_supplement"):
    f1_name = files[0].name.rsplit(".", 1)[0]
    f2_name = files[1].name.rsplit(".", 1)[0]

    df1_raw = handle_file_upload(files[0], f"{file_key}_f1", "划分路径")
    df2_raw = handle_file_upload(files[1], f"{file_key}_f2", "划分路径")
    if df1_raw is None or df2_raw is None:
        return None

    c1 = classify_stage(df1_raw)
    c2 = classify_stage(df2_raw)

    if c1 == "stage1" and c2 == "stage2":
        stage1_df, stage2_df = df1_raw, df2_raw
        st.info(f"自动识别: {f1_name} → 第一阶段(补充), {f2_name} → 第二阶段(路径)")
    elif c1 == "stage2" and c2 == "stage1":
        stage1_df, stage2_df = df2_raw, df1_raw
        st.info(f"自动识别: {f2_name} → 第一阶段(补充), {f1_name} → 第二阶段(路径)")
    else:
        st.warning("无法自动识别阶段，请手动选择：")
        choice = st.radio("哪个是第一阶段（补充列来源）文件？", [f1_name, f2_name], horizontal=True, key=f"{file_key}_pick")
        stage1_df, stage2_df = (df1_raw, df2_raw) if choice == f1_name else (df2_raw, df1_raw)

    p_mapping_s2, _ = detect_path_columns(stage2_df)
    p_mapping_s1, _ = detect_path_columns(stage1_df)

    s2_name_col = p_mapping_s2.get("enterprise_name")
    s1_name_col = p_mapping_s1.get("enterprise_name")
    if not s2_name_col or not s1_name_col:
        st.error("两个阶段都未找到企业名称列")
        return None

    supplement_fields = ["has_rd_team", "has_product_images", "is_core_supplier"]
    missing_from_s2 = [f for f in supplement_fields if f not in p_mapping_s2]
    has_in_s1 = {f: p_mapping_s1.get(f) for f in supplement_fields if f in p_mapping_s1}

    if not missing_from_s2:
        st.info("第二阶段已包含全部路径字段，无需补充，直接划分路径")
        path_df = compute_paths_for_dataframe(stage2_df, p_mapping_s2)
    else:
        st.info(f"第二阶段缺少 {len(missing_from_s2)} 列: {', '.join(FIELD_LABELS_PATH.get(f, f) for f in missing_from_s2)}")
        st.info(f"从第一阶段补充: {', '.join(FIELD_LABELS_PATH.get(f, f) for f in has_in_s1.keys())}")

        enriched = stage2_df.copy()
        field_to_s1col = {}
        for f in missing_from_s2:
            if f in has_in_s1 and has_in_s1[f]:
                field_to_s1col[f] = has_in_s1[f]

        if field_to_s1col:
            supplement_data = stage1_df[[s1_name_col] + list(field_to_s1col.values())].copy()
            supplement_data = supplement_data.rename(columns={v: k for k, v in field_to_s1col.items()})
            enriched = enriched.merge(supplement_data, on=s2_name_col, how="left", suffixes=("", "_supplement"))
            for f in missing_from_s2:
                if f in enriched.columns and f"{f}_supplement" in enriched.columns:
                    enriched[f] = enriched[f].fillna(enriched[f"{f}_supplement"])
                    enriched.drop(columns=[f"{f}_supplement"], inplace=True)

            for f in missing_from_s2:
                if f not in p_mapping_s2 and f in enriched.columns:
                    p_mapping_s2[f] = f

        path_df = compute_paths_for_dataframe(enriched, p_mapping_s2)

        matched = path_df["出海路径"].notna().sum() if "出海路径" in path_df.columns else 0
        total = len(path_df)
        st.success(f"路径划分完成！共 {total} 家企业，匹配率 {matched}/{total} ({matched/total*100:.1f}%)")

    name_col = p_mapping_s2.get("enterprise_name")
    if name_col and name_col in path_df.columns and name_col != "企业名称":
        path_df.drop(columns=[name_col], inplace=True)

    supplement_rename = {"has_rd_team": "研发团队", "has_product_images": "高清产品图", "is_core_supplier": "核心供应商"}
    path_df = path_df.rename(columns={k: v for k, v in supplement_rename.items() if k in path_df.columns})

    with st.expander("  路径划分结果", expanded=True):
        st.dataframe(path_df.head(15), use_container_width=True)

        if "出海路径" in path_df.columns:
            st.markdown("**路径分布：**")
            path_dist = path_df["出海路径"].value_counts().sort_index()
            cols = st.columns(min(len(path_dist), 6))
            for i, (p, cnt) in enumerate(path_dist.items()):
                cols[i % len(cols)].metric(p, cnt)

    st.download_button(
        "  下载路径结果",
        data=path_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="路径划分结果.csv",
        mime="text/csv",
    )

    return path_df


def process_two_stage_files(files, file_key="two_stage"):
    f1_name = files[0].name.rsplit(".", 1)[0]
    f2_name = files[1].name.rsplit(".", 1)[0]

    df1_raw = handle_file_upload(files[0], f"{file_key}_f1", "得分等级+路径")
    df2_raw = handle_file_upload(files[1], f"{file_key}_f2", "得分等级+路径")
    if df1_raw is None or df2_raw is None:
        return None

    c1 = classify_stage(df1_raw)
    c2 = classify_stage(df2_raw)

    if c1 == "stage1" and c2 == "stage2":
        stage1_file, stage2_file = files[0], files[1]
        stage1_df, stage2_df = df1_raw, df2_raw
        st.info(f"自动识别: {f1_name} → 第一阶段(评分), {f2_name} → 第二阶段(路径)")
    elif c1 == "stage2" and c2 == "stage1":
        stage1_file, stage2_file = files[1], files[0]
        stage1_df, stage2_df = df2_raw, df1_raw
        st.info(f"自动识别: {f2_name} → 第一阶段(评分), {f1_name} → 第二阶段(路径)")
    else:
        st.warning("无法自动识别阶段，请手动选择：")
        choice = st.radio("哪个是第一阶段（评分）文件？", [f1_name, f2_name], horizontal=True, key=f"{file_key}_pick")
        if choice == f1_name:
            stage1_df, stage2_df = df1_raw, df2_raw
        else:
            stage1_df, stage2_df = df2_raw, df1_raw

    st.subheader("  第一阶段 — 评分字段识别")
    q_mapping, q_extra = detect_questionnaire_columns(stage1_df)
    st.text(get_detection_summary_questionnaire(stage1_df, q_mapping, q_extra))
    score_df = compute_scores_for_dataframe(stage1_df, q_mapping)
    st.success(f"评分完成！共 {len(score_df)} 家企业")

    st.subheader("  第二阶段 — 路径字段识别")
    p_mapping, p_extra = detect_path_columns(stage2_df)
    st.text(get_detection_summary_path(stage2_df, p_mapping, p_extra))
    path_df = compute_paths_for_dataframe(stage2_df, p_mapping)
    st.success(f"路径划分完成！共 {len(path_df)} 家企业")

    name_col_s1 = q_mapping.get("enterprise_name", "企业名称")
    name_col_s2 = p_mapping.get("enterprise_name", "企业名称")

    if "企业名称" not in score_df.columns and name_col_s1 not in score_df.columns:
        st.error("第一阶段评分结果中未找到企业名称列，无法合并")
        return score_df
    if "企业名称" not in path_df.columns and name_col_s2 not in path_df.columns:
        st.error("第二阶段路径结果中未找到企业名称列，无法合并")
        return score_df

    score_df = score_df.rename(columns={"企业名称": "_merge_key"}) if "企业名称" in score_df.columns else score_df
    path_df = path_df.rename(columns={"企业名称": "_merge_key"}) if "企业名称" in path_df.columns else path_df

    if "_merge_key" not in score_df.columns:
        score_df.insert(0, "_merge_key", stage1_df[name_col_s1].values)
    if "_merge_key" not in path_df.columns:
        path_df.insert(0, "_merge_key", stage2_df[name_col_s2].values)

    path_cols = [c for c in path_df.columns if c != "_merge_key"]
    merged = score_df.merge(path_df[["_merge_key"] + path_cols], on="_merge_key", how="left")

    matched = merged["出海路径"].notna().sum() if "出海路径" in merged.columns else 0
    total = len(merged)
    match_rate = matched / total * 100 if total > 0 else 0

    merged = merged.rename(columns={"_merge_key": "企业名称"})

    keep_cols = [c for c in ["企业名称", "总分", "等级", "外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套", "主干路径", "出海路径"] if c in merged.columns]
    merged = merged[keep_cols]

    st.info(f"企业名匹配率: {matched}/{total} ({match_rate:.1f}%)")

    with st.expander("  合并结果预览", expanded=True):
        preview_cols = [c for c in ["企业名称", "总分", "等级", "主干路径", "出海路径"] if c in merged.columns]
        st.dataframe(merged[preview_cols].head(15), use_container_width=True)

        if "出海路径" in merged.columns:
            st.markdown("**路径分布：**")
            path_dist = merged["出海路径"].value_counts().sort_index()
            cols = st.columns(min(len(path_dist), 6))
            for i, (path, count) in enumerate(path_dist.items()):
                cols[i % len(cols)].metric(path, count)

    st.download_button(
        "  下载合并结果（得分+等级+路径）",
        data=merged.to_csv(index=False).encode("utf-8-sig"),
        file_name="合并结果_得分等级路径.csv",
        mime="text/csv",
    )

    return merged


if len(uploaded_files) == 1:
    result_df = process_single_file(uploaded_files[0], mode, "main")
    if result_df is None:
        st.stop()

    st.session_state["main_data"] = result_df
    st.session_state["region_name"] = uploaded_files[0].name.rsplit(".", 1)[0]

    tab1, tab2, tab3 = st.tabs(["  数据总览", "  企业查询", "  报告导出"])

    with tab1:
        render_overview(result_df)
    with tab2:
        render_enterprise_query(result_df)
    with tab3:
        st.subheader("  导出分析报告")
        region_input = st.text_input("报告中的地区名称", value=st.session_state.get("region_name", ""))
        if st.button("  生成报告", type="primary"):
            with st.spinner("正在生成报告..."):
                report_path = generate_report(result_df, region_name=region_input)
            st.success("报告已生成!")
            st.download_button(
                "  下载报告",
                data=open(report_path, "rb").read(),
                file_name=report_path.split("/")[-1].split("\\")[-1],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

else:
    if mode == "得分等级+路径" and len(uploaded_files) == 2:
        result_df = process_two_stage_files(uploaded_files, "two_stage")
        if result_df is None:
            st.stop()

        st.session_state["main_data"] = result_df
        st.session_state["region_name"] = "合并结果"

        tab1, tab2, tab3 = st.tabs(["  数据总览", "  企业查询", "  报告导出"])

        with tab1:
            render_overview(result_df)
        with tab2:
            render_enterprise_query(result_df)
        with tab3:
            st.subheader("  导出分析报告")
            region_input = st.text_input("报告中的地区名称", value=st.session_state.get("region_name", ""))
            if st.button("  生成报告", type="primary"):
                with st.spinner("正在生成报告..."):
                    report_path = generate_report(result_df, region_name=region_input)
                st.success("报告已生成!")
                st.download_button(
                    "  下载报告",
                    data=open(report_path, "rb").read(),
                    file_name=report_path.split("/")[-1].split("\\")[-1],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
    elif mode == "划分路径" and len(uploaded_files) == 2:
        result_df = process_path_with_supplement(uploaded_files, "path_supplement")
        if result_df is None:
            st.stop()

        st.session_state["main_data"] = result_df
        st.session_state["region_name"] = "路径划分"

        tab1, tab2, tab3 = st.tabs(["  数据总览", "  企业查询", "  报告导出"])

        with tab1:
            render_overview(result_df)
        with tab2:
            render_enterprise_query(result_df)
        with tab3:
            st.subheader("  导出分析报告")
            region_input = st.text_input("报告中的地区名称", value=st.session_state.get("region_name", ""))
            if st.button("  生成报告", type="primary"):
                with st.spinner("正在生成报告..."):
                    report_path = generate_report(result_df, region_name=region_input)
                st.success("报告已生成!")
                st.download_button(
                    "  下载报告",
                    data=open(report_path, "rb").read(),
                    file_name=report_path.split("/")[-1].split("\\")[-1],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
    else:
        all_results = {}
        for f in uploaded_files:
            name = f.name.rsplit(".", 1)[0]
            with st.spinner(f"正在处理 {name}..."):
                result = process_single_file(f, mode, f"multi_{name}")
            if result is not None:
                all_results[name] = result

        if not all_results:
            st.error("所有文件处理失败")
            st.stop()

        st.success(f"成功处理 {len(all_results)} 个文件: {', '.join(all_results.keys())}")

        tab1, tab2, tab3, tab4 = st.tabs(["  数据总览", "  企业查询", "  跨地区对比", "  报告导出"])

        with tab1:
            sel = st.selectbox("选择地区", list(all_results.keys()), key="ov_region")
            render_overview(all_results[sel])
        with tab2:
            sel = st.selectbox("选择地区查询", list(all_results.keys()), key="eq_region")
            render_enterprise_query(all_results[sel])
        with tab3:
            render_comparison(all_results)
        with tab4:
            st.subheader("  导出分析报告")
            export_mode = st.radio("导出模式", ["单个地区", "全部地区"], horizontal=True)
            if export_mode == "单个地区":
                sel = st.selectbox("选择地区", list(all_results.keys()), key="exp_region")
                if st.button("  生成报告", type="primary", key="gen_single"):
                    with st.spinner("正在生成报告..."):
                        report_path = generate_report(all_results[sel], region_name=sel)
                    st.success("报告已生成!")
                    st.download_button(
                        "  下载报告", data=open(report_path, "rb").read(),
                        file_name=report_path.split("/")[-1].split("\\")[-1],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
            else:
                if st.button("  生成全部报告", type="primary", key="gen_all"):
                    for rname, rdf in all_results.items():
                        with st.spinner(f"正在生成 {rname} 报告..."):
                            rpath = generate_report(rdf, region_name=rname)
                        st.download_button(
                            f"  下载 {rname} 报告", data=open(rpath, "rb").read(),
                            file_name=rpath.split("/")[-1].split("\\")[-1],
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_{rname}",
                        )
