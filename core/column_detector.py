import re
import pandas as pd
from config import GRADE_VALUES, PATH_PATTERN
from utils.normalize import normalize


KEYWORD_RULES = {
    "enterprise_name": {
        "keywords": ["企业名称", "公司名称", "企业全称", "单位名称", "公司全称", "名称"],
        "priority": 1,
    },
    "grade": {
        "keywords": ["等级", "评级", "级别", "等级评定"],
        "priority": 2,
    },
    "path": {
        "keywords": ["路径", "出海路径", "划分路径", "路线"],
        "priority": 3,
    },
    "total_score": {
        "keywords": ["总分", "综合分", "综合评分", "总评分"],
        "priority": 4,
    },
    "foreign_trade": {
        "keywords": ["外贸基础", "外贸能力", "外贸"],
        "priority": 5,
    },
    "ecommerce_ops": {
        "keywords": ["电商运营", "电商能力", "电商"],
        "priority": 6,
    },
    "cooperation": {
        "keywords": ["合作配合", "配合意愿", "意愿", "合作"],
        "priority": 7,
    },
    "production": {
        "keywords": ["产能承接", "产能配套", "产能"],
        "priority": 8,
    },
    "region": {
        "keywords": ["所属地区", "地区", "区域", "县区"],
        "priority": 9,
    },
    "industry": {
        "keywords": ["产业集群", "产业", "行业"],
        "priority": 10,
    },
    "product_category": {
        "keywords": ["主营产品", "产品类别", "产品类型", "主营"],
        "priority": 11,
    },
    "contact": {
        "keywords": ["联系人", "负责人"],
        "priority": 12,
    },
    "phone": {
        "keywords": ["联系电话", "电话", "手机", "联系方式"],
        "priority": 13,
    },
}


def _match_keyword(col_name, keywords):
    normalized = normalize(col_name)
    for kw in keywords:
        if normalize(kw) in normalized:
            return True
    return False


def _validate_by_values(series, target, max_sample=50):
    sample = series.dropna().head(max_sample).apply(lambda x: normalize(x))
    if len(sample) == 0:
        return 0.0

    if target == "grade":
        normalized = sample.str.upper().str.replace("级", "", regex=False)
        matches = normalized.isin({"A", "B", "C", "D", "E", "F"})
        return matches.mean()

    if target == "path":
        matches = sample.str.upper().str.match(r"^[A-F][12]$")
        return matches.mean()

    if target in ("total_score", "foreign_trade", "ecommerce_ops", "cooperation", "production"):
        numeric = pd.to_numeric(sample.str.replace(r"[^\d.\-]", "", regex=True), errors="coerce")
        valid_ratio = numeric.notna().mean()
        if valid_ratio > 0.5:
            vals = numeric.dropna()
            if target == "total_score":
                in_range = ((vals >= 0) & (vals <= 100)).mean()
            elif target == "foreign_trade":
                in_range = ((vals >= 0) & (vals <= 25)).mean()
            elif target == "ecommerce_ops":
                in_range = ((vals >= 0) & (vals <= 23)).mean()
            elif target == "cooperation":
                in_range = ((vals >= 0) & (vals <= 35)).mean()
            elif target == "production":
                in_range = ((vals >= 0) & (vals <= 17)).mean()
            else:
                in_range = 0
            return valid_ratio * in_range
        return 0.0

    return 0.0


def detect_columns(df):
    columns = list(df.columns)
    mapping = {}
    used_cols = set()

    candidates = []
    for col in columns:
        for target, rule in KEYWORD_RULES.items():
            if _match_keyword(col, rule["keywords"]):
                val_score = _validate_by_values(df[col], target)
                combined_score = rule["priority"] * 0.6 + (1 - val_score) * 0.4
                if val_score > 0.3:
                    combined_score -= 2.0
                candidates.append((col, target, combined_score, val_score))

    candidates.sort(key=lambda x: x[2])

    for col, target, score, val_score in candidates:
        if col not in used_cols and target not in mapping:
            mapping[target] = col
            used_cols.add(col)

    if "enterprise_name" not in mapping:
        for col in columns:
            if df[col].dtype == "object":
                non_null = df[col].dropna().apply(lambda x: normalize(x))
                if len(non_null) > 0 and non_null.str.len().mean() > 3:
                    mapping["enterprise_name"] = col
                    used_cols.add(col)
                    break

    if "grade" not in mapping:
        for col in columns:
            if col not in used_cols:
                val = _validate_by_values(df[col], "grade")
                if val > 0.5:
                    mapping["grade"] = col
                    used_cols.add(col)
                    break

    if "path" not in mapping:
        for col in columns:
            if col not in used_cols:
                val = _validate_by_values(df[col], "path")
                if val > 0.5:
                    mapping["path"] = col
                    used_cols.add(col)
                    break

    extra_cols = [c for c in columns if c not in used_cols]
    return mapping, extra_cols


def validate_mapping(df, mapping):
    issues = []
    if "enterprise_name" in mapping:
        col = mapping["enterprise_name"]
        nunique = df[col].dropna().apply(lambda x: normalize(x)).nunique()
        total = len(df)
        if nunique < total * 0.5:
            issues.append(f"'{col}' 中重复值较多（{nunique}/{total}），可能不是企业名称列")

    if "grade" in mapping:
        col = mapping["grade"]
        vals = df[col].dropna().apply(lambda x: normalize(x)).str.upper().str.replace("级", "", regex=False)
        valid = vals.isin({"A", "B", "C", "D", "E", "F"})
        invalid_count = (~valid).sum()
        if invalid_count > 0:
            unique_invalid = vals[~valid].unique()[:5]
            issues.append(f"'{col}' 中有 {invalid_count} 个值不符合等级格式: {list(unique_invalid)}")

    if "path" in mapping:
        col = mapping["path"]
        vals = df[col].dropna().apply(lambda x: normalize(x)).str.upper()
        valid = vals.str.match(r"^[A-F][12]$") | vals.isin(["无匹配路径"])
        invalid_count = (~valid).sum()
        if invalid_count > 0:
            unique_invalid = vals[~valid].unique()[:10]
            issues.append(f"'{col}' 中有 {invalid_count} 个值不符合路径格式: {list(unique_invalid)}")

    if "total_score" in mapping:
        col = mapping["total_score"]
        numeric = pd.to_numeric(df[col], errors="coerce")
        out_of_range = ((numeric < 0) | (numeric > 100)).sum()
        if out_of_range > 0:
            issues.append(f"'{col}' 中有 {out_of_range} 个值超出0-100范围")

    return issues


def get_detection_summary(df, mapping, extra_cols):
    summary = []
    for target, col in mapping.items():
        sample_vals = df[col].dropna().head(3).tolist()
        summary.append(f"  {target} → '{col}' (样例: {sample_vals})")
    if extra_cols:
        summary.append(f"  未识别列({len(extra_cols)}): {extra_cols[:5]}{'...' if len(extra_cols) > 5 else ''}")
    return "\n".join(summary)
