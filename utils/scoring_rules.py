SCORE_DIMENSIONS = {
    "外贸基础能力": {
        "max_score": 25,
        "sub_items": [
            {"name": "拥有外贸出口经验", "max": 7, "rule": "有=7分；无=0分", "field": "has_export_experience"},
            {"name": "是否为专精特新企业", "max": 2, "rule": "是=2分；否=0分", "field": "is_specialized_enterprise"},
            {"name": "是否为产业带代表性企业", "max": 2, "rule": "是=2分；否=0分", "field": "is_industry_representative"},
            {"name": "是否为拥有创新产品的企业", "max": 2, "rule": "是=2分；否=0分", "field": "has_innovative_product"},
            {"name": "广交会参展/其他国际展会", "max": 2, "rule": "任一为是=2分；均为否=0分", "field": "has_exhibition_experience"},
            {"name": "企业上年度出口额(美元)", "max": 10,
             "rule": "50万美元及以上=10分；10万-49.9万=6分；1万-9.9万=3分；1万以下/无=0分",
             "field": "export_amount"},
        ],
    },
    "电商运营能力": {
        "max_score": 23,
        "sub_items": [
            {"name": "拥有电商供货经验(国内/跨境均可)", "max": 8, "rule": "是=8分；否=0分", "field": "has_ecommerce_experience"},
            {"name": "拥有专属电商团队", "max": 8, "rule": "是=8分；否=0分", "field": "has_ecommerce_team"},
            {"name": "电商平台及店铺数量", "max": 7,
             "rule": "3个及以上=7分；2个=4分；1个=2分；无=0分",
             "field": "ecommerce_platform_count"},
        ],
    },
    "合作配合意愿": {
        "max_score": 35,
        "sub_items": [
            {"name": "愿意产品免费入驻本地展厅展示", "max": 6, "rule": "是=6分；否=0分", "field": "willing_showroom"},
            {"name": "愿意接受跨境小批量多品种订单", "max": 6, "rule": "是=6分；否=0分", "field": "willing_small_batch"},
            {"name": "愿意派员参加后续跨境电商培训(人数)", "max": 7,
             "rule": "3人及以上=7分；2人=4分；1人=2分；否=0分",
             "field": "willing_training_count"},
            {"name": "愿意配合提供产品高清素材参数包装信息", "max": 8, "rule": "是=8分；否=0分", "field": "willing_product_materials"},
            {"name": "有专人可对接后续合作事宜(人数)", "max": 8,
             "rule": "2人及以上=8分；1人=4分；无=0分",
             "field": "liaison_count"},
        ],
    },
    "产能承接配套": {
        "max_score": 17,
        "sub_items": [
            {"name": "企业目前月产能可预留新渠道订单比例", "max": 7,
             "rule": "30%及以上=7分；15%-29%=5分；5%-14%=2分；5%以下/无=0分",
             "field": "capacity_reservation_ratio"},
            {"name": "企业上年度电商总销售额(含跨境/国内)(美元)", "max": 10,
             "rule": "跨境电商10万+且有国内配套=10分；仅跨境/仅国内=3分；无=0分",
             "field": "ecommerce_sales_amount"},
        ],
    },
}

GRADE_THRESHOLDS = [
    ("A级", 75, 100, "核心重点培育企业"),
    ("B级", 60, 74, "重点调研培育企业"),
    ("C级", 45, 59, "优先培育企业"),
    ("D级", 30, 44, "储备培育企业"),
    ("E级", 15, 29, "观察培育企业"),
    ("F级", 0, 14, "基础培育企业"),
]

FIELD_MAPPING = {
    "has_export_experience": {"keywords": ["外贸出口经验", "出口经验", "是否有外贸"], "type": "bool"},
    "is_specialized_enterprise": {"keywords": ["专精特新"], "type": "bool"},
    "is_industry_representative": {"keywords": ["产业带代表"], "type": "bool"},
    "has_innovative_product": {"keywords": ["创新产品"], "type": "bool"},
    "has_exhibition_experience": {"keywords": ["广交会", "国际展会", "参展"], "type": "bool"},
    "export_amount": {"keywords": ["出口额", "上年度出口"], "type": "export_amount"},
    "has_ecommerce_experience": {"keywords": ["电商供货经验", "电商经验"], "type": "bool"},
    "has_ecommerce_team": {"keywords": ["专属电商团队", "电商团队"], "type": "bool"},
    "ecommerce_platform_count": {"keywords": ["电商平台", "店铺数量", "平台数量"], "type": "platform_count"},
    "willing_showroom": {"keywords": ["展厅展示", "免费入驻", "展厅"], "type": "bool"},
    "willing_small_batch": {"keywords": ["小批量", "多品种订单"], "type": "bool"},
    "willing_training_count": {"keywords": ["培训", "参加培训"], "type": "training_count"},
    "willing_product_materials": {"keywords": ["产品素材", "高清素材", "参数", "包装信息"], "type": "bool"},
    "liaison_count": {"keywords": ["专人对接", "对接合作", "专人"], "type": "liaison_count"},
    "capacity_reservation_ratio": {"keywords": ["产能预留", "预留比例", "产能比例"], "type": "capacity_ratio"},
    "ecommerce_sales_amount": {"keywords": ["电商销售额", "电商总销售额", "电商销售"], "type": "ecommerce_sales"},
}


def score_bool(value):
    from utils.normalize import normalize_yes_no
    result = normalize_yes_no(value)
    return 1 if result == "是" else 0


def score_export_amount(value):
    from utils.normalize import normalize
    import re
    s = normalize(value)
    if "无" in s or "以下" in s:
        return 0
    s = s.replace("美元", "").replace("$", "").strip()
    # Handle ranges like "10-49.9万" → use the lower bound, keep 万 for multiplier
    range_match = re.match(r'([\d.]+)\s*[-~]\s*([\d.]+)(.*)', s)
    if range_match:
        s = range_match.group(1) + range_match.group(3)
    s = s.replace("万", "0000").replace("及以上", "").replace("以上", "").strip()
    try:
        num = float("".join(c for c in s if c.isdigit() or c == "."))
    except (ValueError, TypeError):
        return 0
    if num >= 500000:
        return 10
    elif num >= 100000:
        return 6
    elif num >= 10000:
        return 3
    return 0


def score_platform_count(value):
    from utils.normalize import normalize, normalize_count
    s = normalize(value)
    if "3" in s and ("以上" in s or "个" in s or s in ["3", "4", "5", "6", "7", "8", "9", "10"]):
        return 7
    if s in ["2", "2个"] or (s.startswith("2") and "个" in s):
        return 4
    if s in ["1", "1个"] or (s.startswith("1") and "个" in s):
        return 2
    num = normalize_count(s)
    if num >= 3:
        return 7
    elif num == 2:
        return 4
    elif num == 1:
        return 2
    return 0


def score_training_count(value):
    from utils.normalize import normalize, normalize_count
    s = normalize(value)
    if s in ["否", "无", "不参加", "0"]:
        return 0
    num = normalize_count(s)
    if num >= 3:
        return 7
    elif num == 2:
        return 4
    elif num == 1:
        return 2
    return 0


def score_liaison_count(value):
    from utils.normalize import normalize, normalize_count
    s = normalize(value)
    if s in ["否", "无", "0"]:
        return 0
    num = normalize_count(s)
    if num >= 2:
        return 8
    elif num == 1:
        return 4
    return 0


def score_capacity_ratio(value):
    from utils.normalize import normalize, normalize_percent
    s = normalize(value)
    if "不清楚" in s:
        return 0
    num = normalize_percent(s)
    if num >= 30:
        return 7
    elif num >= 15:
        return 5
    elif num >= 5:
        return 2
    return 0


def score_ecommerce_sales(value):
    from utils.normalize import normalize
    import re
    s = normalize(value).lower()
    if re.search(r'(^|[^0-9])0([^0-9]|$)', s) or "无任何" in s or "无" in s or "没有" in s:
        return 0
    if "不足" in s or "有销售额" in s:
        return 3
    s_num = s.replace("美元", "").replace("$", "").replace("及以上", "").replace("以上", "").strip()
    s_num = s_num.replace("万", "0000")
    try:
        num = float("".join(c for c in s_num if c.isdigit() or c == "."))
        if num >= 100000:
            return 10
        elif num > 0:
            return 3
    except (ValueError, TypeError):
        pass
    return 0


SCORE_FUNCTIONS = {
    "bool": score_bool,
    "export_amount": score_export_amount,
    "platform_count": score_platform_count,
    "training_count": score_training_count,
    "liaison_count": score_liaison_count,
    "capacity_ratio": score_capacity_ratio,
    "ecommerce_sales": score_ecommerce_sales,
}


def calculate_scores(row_data):
    results = {}
    total = 0

    for dim_name, dim_info in SCORE_DIMENSIONS.items():
        dim_score = 0
        for item in dim_info["sub_items"]:
            field = item["field"]
            raw_value = row_data.get(field, "")
            field_type = FIELD_MAPPING[field]["type"]
            score_func = SCORE_FUNCTIONS.get(field_type, lambda v: 0)
            if field_type == "bool":
                score = score_func(raw_value) * item["max"]
            else:
                score = min(score_func(raw_value), item["max"])
            results[field] = {"raw": raw_value, "score": score, "max": item["max"], "name": item["name"]}
            dim_score += score
        results[dim_name] = {"score": dim_score, "max": dim_info["max_score"]}
        total += dim_score

    results["总分"] = total
    return results


def determine_grade(total_score):
    if total_score is None:
        return None
    for grade, low, high, desc in GRADE_THRESHOLDS:
        if low <= total_score <= high:
            return grade
    return None


def get_score_breakdown():
    lines = []
    for dim, info in SCORE_DIMENSIONS.items():
        lines.append(f"【{dim}】满分{info['max_score']}分")
        for item in info["sub_items"]:
            lines.append(f"  - {item['name']}: {item['rule']}")
    return "\n".join(lines)


def get_grade_thresholds():
    lines = ["等级划分标准（总分100分）:"]
    for grade, low, high, desc in GRADE_THRESHOLDS:
        lines.append(f"  {grade}: {low}-{high}分 ({desc})")
    return "\n".join(lines)
