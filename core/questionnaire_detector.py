import re
import pandas as pd
from utils.scoring_rules import FIELD_MAPPING, SCORE_DIMENSIONS, calculate_scores, determine_grade
from utils.normalize import normalize, normalize_yes_no, normalize_number, normalize_count, normalize_percent


REQUIRED_SCORING_FIELDS = [
    "has_export_experience", "is_specialized_enterprise", "is_industry_representative",
    "has_innovative_product", "has_exhibition_experience", "export_amount",
    "has_ecommerce_experience", "has_ecommerce_team", "ecommerce_platform_count",
    "willing_showroom", "willing_small_batch", "willing_training_count",
    "willing_product_materials", "liaison_count",
    "capacity_reservation_ratio", "ecommerce_sales_amount",
]

FIELD_LABELS = {
    "enterprise_name": "企业名称",
    "has_export_experience": "外贸出口经验", "is_specialized_enterprise": "专精特新",
    "is_industry_representative": "产业带代表性", "has_innovative_product": "创新产品",
    "has_exhibition_experience": "展会参展", "export_amount": "上年度出口额",
    "has_ecommerce_experience": "电商供货经验", "has_ecommerce_team": "专属电商团队",
    "ecommerce_platform_count": "平台店铺数量", "willing_showroom": "展厅展示",
    "willing_small_batch": "小批量订单", "willing_training_count": "培训人数",
    "willing_product_materials": "产品素材参数", "liaison_count": "对接人数",
    "capacity_reservation_ratio": "产能预留比例", "ecommerce_sales_amount": "电商销售额",
}


def detect_questionnaire_columns(df):
    columns = list(df.columns)
    mapping = {}
    used_cols = set()

    name_keywords = ["企业名称", "公司名称", "企业全称", "单位名称", "名称"]
    for col in columns:
        norm_col = normalize(col)
        for kw in name_keywords:
            if normalize(kw) in norm_col:
                mapping["enterprise_name"] = col
                used_cols.add(col)
                break
        if "enterprise_name" in mapping:
            break

    for field_key, field_info in FIELD_MAPPING.items():
        best_col = None
        best_score = 0
        for col in columns:
            if col in used_cols:
                continue
            norm_col = normalize(col)
            for kw in field_info["keywords"]:
                if normalize(kw) in norm_col:
                    val_score = _validate_field(df[col], field_info["type"])
                    score = 1.0 + val_score
                    if score > best_score:
                        best_score = score
                        best_col = col
                    break
        if best_col and best_score > 0.5:
            mapping[field_key] = best_col
            used_cols.add(best_col)

    extra_cols = [c for c in columns if c not in used_cols]
    return mapping, extra_cols


def _validate_field(series, field_type):
    sample = series.dropna().head(30).apply(lambda x: normalize(x))
    if len(sample) == 0:
        return 0.0

    if field_type == "bool":
        positive_vals = {"是", "有", "yes", "y", "true", "1"}
        negative_vals = {"否", "无", "没有", "no", "n", "false", "0"}
        normalized = sample.str.lower().str.strip()
        match_count = normalized.isin(positive_vals | negative_vals).sum()
        return match_count / len(sample)

    if field_type in ("export_amount", "ecommerce_sales"):
        has_number = sample.str.contains(r"\d", regex=True).sum()
        return has_number / len(sample)

    if field_type in ("platform_count", "training_count", "liaison_count"):
        has_number = sample.str.contains(r"\d", regex=True).sum()
        return has_number / len(sample)

    if field_type == "capacity_ratio":
        has_percent = sample.str.contains(r"\d", regex=True).sum()
        return has_percent / len(sample)

    return 0.0


def check_required_fields(mapping, mode="score"):
    missing = []
    if mode in ("score", "both"):
        for field in REQUIRED_SCORING_FIELDS:
            if field not in mapping:
                missing.append(FIELD_LABELS.get(field, field))
    if mode in ("path", "both"):
        path_required = ["direction_intent", "customer_profile"]
        path_labels = {"direction_intent": "方向意图", "customer_profile": "客户画像"}
        for field in path_required:
            if field not in mapping:
                missing.append(path_labels.get(field, field))
    return missing


def compute_scores_for_dataframe(df, col_mapping):
    results = []
    enterprise_col = col_mapping.get("enterprise_name")

    for idx, row in df.iterrows():
        row_data = {}
        for field_key, col_name in col_mapping.items():
            if field_key == "enterprise_name":
                continue
            row_data[field_key] = row.get(col_name, "")

        score_result = calculate_scores(row_data)
        flat = {}
        for k, v in score_result.items():
            if isinstance(v, dict) and "score" in v:
                flat[k] = v["score"]
            else:
                flat[k] = v
        results.append(flat)

    score_df = pd.DataFrame(results)

    if enterprise_col:
        score_df.insert(0, "企业名称", df[enterprise_col].values)

    if "总分" in score_df.columns:
        score_df["等级"] = score_df["总分"].apply(determine_grade)

    return score_df


def get_detection_summary_questionnaire(df, mapping, extra_cols):
    summary = []
    if "enterprise_name" in mapping:
        col = mapping["enterprise_name"]
        sample = df[col].dropna().head(3).tolist()
        summary.append(f"  企业名称 → '{col}' (样例: {sample})")

    detected_fields = {k: v for k, v in mapping.items() if k != "enterprise_name"}
    summary.append(f"  识别到 {len(detected_fields)}/{len(REQUIRED_SCORING_FIELDS)} 个评分字段")

    found_dims = set()
    for field_key in detected_fields:
        for dim_name, dim_info in SCORE_DIMENSIONS.items():
            for item in dim_info["sub_items"]:
                if item["field"] == field_key:
                    found_dims.add(dim_name)

    for dim_name, dim_info in SCORE_DIMENSIONS.items():
        dim_fields = [item["field"] for item in dim_info["sub_items"]]
        found_count = sum(1 for f in dim_fields if f in detected_fields)
        total_count = len(dim_fields)
        status = "✓" if found_count == total_count else f"⚠ {found_count}/{total_count}"
        summary.append(f"  {status} {dim_name}")

    missing = check_required_fields(mapping, mode="score")
    if missing:
        summary.append(f"\n  ✗ 缺少必填字段({len(missing)}): {missing}")

    if extra_cols:
        summary.append(f"  未匹配列({len(extra_cols)}): {extra_cols[:5]}{'...' if len(extra_cols) > 5 else ''}")

    return "\n".join(summary)


STAGE1_MARKER_KEYWORDS = ["外贸出口经验", "专精特新", "产业带代表", "创新产品", "广交会", "电商供货经验", "展厅展示", "小批量"]
STAGE2_MARKER_KEYWORDS = ["方向意图", "客户画像", "SKU", "MOQ", "起订量", "主营产品所属大类"]


def _count_keyword_hits(df, keywords):
    hit_cols = 0
    for col in df.columns:
        norm = normalize(col)
        for kw in keywords:
            if normalize(kw) in norm:
                hit_cols += 1
                break
    return hit_cols


def is_stage1_dataframe(df):
    hits = _count_keyword_hits(df, STAGE1_MARKER_KEYWORDS)
    return hits >= 3


def is_stage2_dataframe(df):
    hits = _count_keyword_hits(df, STAGE2_MARKER_KEYWORDS)
    return hits >= 3


def classify_stage(df):
    s1 = is_stage1_dataframe(df)
    s2 = is_stage2_dataframe(df)
    if s1 and not s2:
        return "stage1"
    if s2 and not s1:
        return "stage2"
    if s1 and s2:
        return "both"
    return "unknown"
