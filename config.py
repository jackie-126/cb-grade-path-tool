import os

GRADE_ORDER = ["A级", "B级", "C级", "D级", "E级", "F级"]

GRADE_VALUES = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}

PATH_NAMES = {
    "A1": "B2C精品模式",
    "A2": "B2C铺货模式",
    "B1": "B2B现货批发",
    "B2": "B2B定制生产",
    "C1": "核心供应商代发",
    "C2": "一般供应商配送",
    "D1": "独立站+消费品",
    "D2": "独立站+工业品",
    "E1": "大客户招投标",
    "E2": "认证准入型",
    "F1": "学习了解型",
    "F2": "暂无意愿型",
}

PATH_PATTERN = r"^[A-F][12]$"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
