import pandas as pd
import streamlit as st
from core.column_detector import detect_columns, validate_mapping, get_detection_summary


def load_excel(uploaded_file):
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            return df
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            return df
    except Exception:
        try:
            uploaded_file.seek(0)
            if name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, encoding="gbk")
            else:
                df = pd.read_excel(uploaded_file, engine="xlrd")
            return df
        except Exception as e:
            st.error(f"无法读取文件: {e}")
            return None


def standardize_data(df, mapping):
    result = pd.DataFrame()

    col_map = {
        "enterprise_name": "企业名称",
        "grade": "等级",
        "path": "路径",
        "total_score": "总分",
        "foreign_trade": "外贸基础能力",
        "ecommerce_ops": "电商运营能力",
        "cooperation": "合作配合意愿",
        "production": "产能承接配套",
        "region": "所属地区",
        "industry": "产业集群",
        "product_category": "主营产品类别",
        "contact": "联系人",
        "phone": "联系电话",
    }

    for std_name, orig_col in mapping.items():
        if orig_col in df.columns:
            result[col_map.get(std_name, std_name)] = df[orig_col]

    if "等级" in result.columns:
        result["等级"] = result["等级"].astype(str).str.strip()
        result["等级_排序"] = result["等级"].map({
            "A级": 1, "B级": 2, "C级": 3, "D级": 4, "E级": 5, "F级": 6
        }).fillna(99)

    if "路径" in result.columns:
        result["路径"] = result["路径"].astype(str).str.strip()

    if "总分" in result.columns:
        result["总分"] = pd.to_numeric(
            result["总分"].astype(str).str.replace(r"[^\d.\-]", "", regex=True),
            errors="coerce"
        )

    score_cols = ["外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套"]
    for sc in score_cols:
        if sc in result.columns:
            result[sc] = pd.to_numeric(
                result[sc].astype(str).str.replace(r"[^\d.\-]", "", regex=True),
                errors="coerce"
            )

    if "企业名称" in result.columns:
        result = result.drop_duplicates(subset=["企业名称"], keep="first")

    extra_std_names = []
    for std_name, orig_col in mapping.items():
        if std_name not in col_map and orig_col in df.columns:
            result[orig_col] = df[orig_col]

    return result


def handle_file_upload(uploaded_file, session_key, mode="已有得分等级和路径"):
    df = load_excel(uploaded_file)
    if df is None:
        return None

    st.success(f"文件读取成功: {uploaded_file.name} ({len(df)} 行, {len(df.columns)} 列)")

    if mode in ["划分路径", "得分等级+路径", "计算得分和等级"]:
        return df

    mapping, extra_cols = detect_columns(df)

    st.subheader("智能列识别结果")
    st.text(get_detection_summary(df, mapping, extra_cols))

    issues = validate_mapping(df, mapping)
    if issues:
        for issue in issues:
            st.warning(issue)

    with st.expander("手动修正列映射", expanded=False):
        col_options = ["(不识别)"] + list(df.columns)
        new_mapping = {}
        for target, col in mapping.items():
            label = {
                "enterprise_name": "企业名称",
                "grade": "等级",
                "path": "路径",
                "total_score": "总分",
                "foreign_trade": "外贸基础能力",
                "ecommerce_ops": "电商运营能力",
                "cooperation": "合作配合意愿",
                "production": "产能承接配套",
                "region": "所属地区",
                "industry": "产业集群",
                "product_category": "主营产品类别",
                "contact": "联系人",
                "phone": "联系电话",
            }.get(target, target)
            current_idx = col_options.index(col) if col in col_options else 0
            selected = st.selectbox(
                f"{label}",
                col_options,
                index=current_idx,
                key=f"map_{session_key}_{target}",
            )
            if selected != "(不识别)":
                new_mapping[target] = selected

        if st.button("应用修正", key=f"apply_{session_key}"):
            mapping = new_mapping

    standardized = standardize_data(df, mapping)
    return standardized


def load_multiple_files(uploaded_files):
    datasets = {}
    for f in uploaded_files:
        name = f.name.rsplit(".", 1)[0]
        df = handle_file_upload(f, f"multi_{name}")
        if df is not None:
            datasets[name] = df
    return datasets
