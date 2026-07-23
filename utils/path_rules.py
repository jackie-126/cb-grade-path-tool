MAIN_PATH_RULES = {
    "F": {
        "name": "蓄力/观望型",
        "condition": lambda row: row.get("direction_intent", "") in [
            "想先学习了解，暂不启动", "暂不考虑跨境电商",
        ],
    },
    "E": {
        "name": "垂直大客户型",
        "condition": lambda row: any(
            kw in str(row.get("customer_profile", ""))
            for kw in ["工程公司/项目方", "机构/政府采购"]
        ),
    },
    "A": {
        "name": "B2C平台型",
        "condition": lambda row: row.get("direction_intent", "") == "想在B2C平台跨境电商（亚马逊/Temu/TikTok Shop等）",
    },
    "B": {
        "name": "B2B平台型",
        "condition": lambda row: row.get("direction_intent", "") == "想做B2B平台跨境电商（阿里国际站/中国制造网等）",
    },
    "C": {
        "name": "海外货盘型",
        "condition": lambda row: row.get("direction_intent", "") == "想给跨境电商卖家供货（做供应链/OEM/ODM）",
    },
    "D": {
        "name": "独立站模式",
        "condition": lambda row: row.get("direction_intent", "") in [
            "想做独立站跨境电商", "想通过跨境电商获取海外小B客户线索",
        ],
    },
}

SUB_PATH_RULES = {
    "A": {
        "A1": lambda row: (
            str(row.get("sku_count", "")) == "1—10个"
            and str(row.get("has_rd_team", "")) == "是"
            and str(row.get("has_product_images", "")) == "是"
        ),
        "A2": lambda row: True,
    },
    "B": {
        "B1": lambda row: str(row.get("moq", "")) in ["1,000元以下", "1,000~5,000元"],
        "B2": lambda row: True,
    },
    "C": {
        "C1": lambda row: (
            str(row.get("is_core_supplier", "")) == "是"
            and str(row.get("sku_count", "")) == "1—10个"
        ),
        "C2": lambda row: True,
    },
    "D": {
        "D1": lambda row: any(
            kw in str(row.get("product_category", ""))
            for kw in ["居民消费品", "3C个人消费电子", "农林初级产品"]
        ),
        "D2": lambda row: True,
    },
    "E": {
        "E2": lambda row: "药包材" in str(row.get("product_category", "")) or "医用耗材" in str(row.get("product_category", "")),
        "E1": lambda row: True,
    },
    "F": {
        "F1": lambda row: row.get("direction_intent", "") == "想先学习了解，暂不启动",
        "F2": lambda row: True,
    },
}

MAIN_PATH_TABLE = {
    "A": {"交易模式": "B2C", "目标市场": "北美、西欧、日韩、澳洲"},
    "B": {"交易模式": "B2B", "目标市场": "东南亚、拉美、中东、中东欧、中亚、南亚"},
    "C": {"交易模式": "B2小B", "目标市场": "北美、西欧、澳洲"},
    "D": {"交易模式": "DTC/独立站询盘", "目标市场": "北美、东南亚、西欧、澳洲"},
    "E": {"交易模式": "B2B(大额)/G端", "目标市场": "俄罗斯、中东、中亚、非洲、中东欧"},
    "F": {"交易模式": "未启动", "目标市场": "不适用"},
}


def determine_main_path(row):
    for code in ["F", "E", "A", "B", "C", "D"]:
        if MAIN_PATH_RULES[code]["condition"](row):
            return code
    return "无匹配"


def determine_sub_path(main_code, row):
    if main_code in SUB_PATH_RULES:
        for sub_code, condition in SUB_PATH_RULES[main_code].items():
            if condition(row):
                return sub_code
    return f"{main_code}?"


def determine_full_path(row):
    main = determine_main_path(row)
    sub = determine_sub_path(main, row)
    return f"{main}{sub[-1]}" if sub.endswith("?") else sub


def explain_path(path_code):
    if len(path_code) < 2:
        return "未知路径"
    main_code = path_code[0]
    sub_code = path_code

    main_info = MAIN_PATH_TABLE.get(main_code, {})
    main_name = MAIN_PATH_RULES.get(main_code, {}).get("name", "未知")

    sub_desc = PATH_NAMES.get(sub_code, "未知细分")

    return {
        "路径码": sub_code,
        "主干": f"{main_code} - {main_name}",
        "细分": sub_desc,
        "交易模式": main_info.get("交易模式", "未知"),
        "目标市场": main_info.get("目标市场", "未知"),
    }


from config import PATH_NAMES
