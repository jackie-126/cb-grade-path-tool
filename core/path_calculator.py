import re
import pandas as pd
from utils.normalize import normalize, normalize_sku, normalize_moq


PATH_DIRECTION_FIELDS = {
    "direction_intent": {"keywords": ["方向意图", "想要做跨境电商", "出海方向", "跨境方向"], "type": "direction"},
    "customer_profile": {"keywords": ["客户画像", "客户类型", "目标客户"], "type": "customer"},
    "product_category": {"keywords": ["主营产品", "产品大类", "产品类别", "产品类型"], "type": "product"},
    "sku_count": {"keywords": ["SKU", "sku", "典型SKU"], "type": "sku"},
    "moq": {"keywords": ["MOQ", "moq", "起订量", "最小起订"], "type": "moq"},
    "has_rd_team": {"keywords": ["研发", "设计团队", "独立研发"], "type": "bool"},
    "has_product_images": {"keywords": ["高清产品图", "产品图", "高清图", "参数表"], "type": "bool"},
    "is_core_supplier": {"keywords": ["核心供应商", "稳定供货", "长期供货", "供货承接"], "type": "bool"},
}

PATH_FIELD_LABELS = {
    "enterprise_name": "企业名称", "direction_intent": "方向意图",
    "customer_profile": "客户画像", "product_category": "主营产品",
    "sku_count": "SKU数量", "moq": "最小起订量",
    "has_rd_team": "研发团队", "has_product_images": "高清产品图和参数表",
    "is_core_supplier": "核心供应商",
}


def detect_path_columns(df):
    columns = list(df.columns)
    mapping = {}
    used_cols = set()

    name_keywords = ["企业名称", "公司名称", "企业全称", "名称"]
    for col in columns:
        norm_col = normalize(col)
        for kw in name_keywords:
            if normalize(kw) in norm_col:
                mapping["enterprise_name"] = col
                used_cols.add(col)
                break
        if "enterprise_name" in mapping:
            break

    for field_key, field_info in PATH_DIRECTION_FIELDS.items():
        best_col = None
        best_score = 0
        for col in columns:
            if col in used_cols:
                continue
            norm_col = normalize(col)
            for kw in field_info["keywords"]:
                if normalize(kw) in norm_col:
                    score = 1.0
                    if score > best_score:
                        best_score = score
                        best_col = col
                    break
        if best_col:
            mapping[field_key] = best_col
            used_cols.add(best_col)

    extra_cols = [c for c in columns if c not in used_cols]
    return mapping, extra_cols


def check_required_path_fields(mapping):
    missing = []
    required = ["direction_intent", "customer_profile"]
    labels = {"direction_intent": "方向意图", "customer_profile": "客户画像"}
    for field in required:
        if field not in mapping:
            missing.append(labels[field])
    return missing


def determine_main_path(direction_intent, customer_profile):
    s_intent = normalize(direction_intent) if pd.notna(direction_intent) else ""
    s_customer = normalize(customer_profile) if pd.notna(customer_profile) else ""

    if "学习了解" in s_intent or "暂不启动" in s_intent or "暂不考虑" in s_intent:
        return "F"
    if "工程公司" in s_customer or "机构/政府采购" in s_customer or "政府采购" in s_customer:
        return "E"
    if "B2C" in s_intent or "跨境平台开店" in s_intent or "亚马逊" in s_intent or "Temu" in s_intent or "TikTok" in s_intent:
        return "A"
    if "B2B" in s_intent or "阿里国际站" in s_intent or "中国制造网" in s_intent:
        return "B"
    if "供货" in s_intent or "供应链" in s_intent or "OEM" in s_intent or "ODM" in s_intent:
        return "C"
    if "独立站" in s_intent or "自主品牌" in s_intent or "小B客户" in s_intent or "海外小B" in s_intent:
        return "D"
    return ""


def determine_sub_path(main_code, row_data):
    if main_code == "A":
        sku_raw = str(row_data.get("sku_count", ""))
        rd_raw = str(row_data.get("has_rd_team", ""))
        img_raw = str(row_data.get("has_product_images", ""))
        sku = normalize(sku_raw)
        rd = normalize(rd_raw)
        img = normalize(img_raw)
        rd_yes = rd.lower() in ["是", "有", "yes"]
        img_yes = img.lower() in ["是", "有", "yes"]
        sku_val = normalize_sku(sku_raw)
        if sku_val <= 10 and rd_yes and img_yes:
            return "A1"
        return "A2"
    elif main_code == "B":
        moq_raw = str(row_data.get("moq", ""))
        moq_val = normalize_moq(moq_raw)
        if moq_val < 5000:
            return "B1"
        return "B2"
    elif main_code == "C":
        core_raw = str(row_data.get("is_core_supplier", ""))
        sku_raw = str(row_data.get("sku_count", ""))
        core = normalize(core_raw)
        sku = normalize(sku_raw)
        core_yes = core.lower() in ["是", "有", "yes"]
        sku_val = normalize_sku(sku_raw)
        if core_yes and sku_val <= 10:
            return "C1"
        return "C2"
    elif main_code == "D":
        product_raw = str(row_data.get("product_category", ""))
        product = normalize(product_raw)
        if any(kw in product for kw in ["居民消费品", "3C", "消费电子", "农林初级产品"]):
            return "D1"
        return "D2"
    elif main_code == "E":
        product_raw = str(row_data.get("product_category", ""))
        product = normalize(product_raw)
        if "药包材" in product or "医用耗材" in product:
            return "E2"
        return "E1"
    elif main_code == "F":
        intent_raw = str(row_data.get("direction_intent", ""))
        intent = normalize(intent_raw)
        if "学习了解" in intent or "暂不启动" in intent:
            return "F1"
        return "F2"
    return ""


def compute_paths_for_dataframe(df, col_mapping):
    results = []
    enterprise_col = col_mapping.get("enterprise_name")

    for idx, row in df.iterrows():
        row_data = {}
        for field_key, col_name in col_mapping.items():
            if field_key == "enterprise_name":
                continue
            row_data[field_key] = row.get(col_name, "")

        direction = row_data.get("direction_intent", "")
        customer = row_data.get("customer_profile", "")

        main_path = determine_main_path(direction, customer)
        full_path = determine_sub_path(main_path, row_data) if main_path else ""

        results.append({
            "主干路径": main_path,
            "出海路径": full_path,
        })

    result_df = pd.DataFrame(results)
    if enterprise_col:
        result_df.insert(0, "企业名称", df[enterprise_col].values)

    return result_df


def get_detection_summary_path(df, mapping, extra_cols):
    summary = []
    if "enterprise_name" in mapping:
        col = mapping["enterprise_name"]
        sample = df[col].dropna().head(3).tolist()
        summary.append(f"  企业名称 → '{col}' (样例: {sample})")

    detected = {k: v for k, v in mapping.items() if k != "enterprise_name"}
    summary.append(f"  识别到 {len(detected)}/{len(PATH_DIRECTION_FIELDS)} 个路径字段")

    for field_key, label in PATH_FIELD_LABELS.items():
        if field_key == "enterprise_name":
            continue
        status = "✓" if field_key in detected else ("✗ 缺少(必须)" if field_key in ["direction_intent", "customer_profile"] else "  (未识别)")
        summary.append(f"  {status} {label}")

    missing = check_required_path_fields(mapping)
    if missing:
        summary.append(f"\n  ✗ 缺少必填字段({len(missing)}): {missing}")

    if extra_cols:
        summary.append(f"  未匹配列({len(extra_cols)}): {extra_cols[:5]}{'...' if len(extra_cols) > 5 else ''}")

    return "\n".join(summary)
