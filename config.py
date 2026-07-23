import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

GRADE_VALUES = {"A级", "B级", "C级", "D级", "E级", "F级"}
GRADE_ORDER = ["A级", "B级", "C级", "D级", "E级", "F级"]
PATH_PATTERN = r"^[A-F][12]$"
SCORE_DIMENSIONS = {
    "外贸基础能力": 25,
    "电商运营能力": 23,
    "合作配合意愿": 35,
    "产能承接配套": 17,
}
TOTAL_MAX_SCORE = 100

PATH_NAMES = {
    "A1": "B2C精品模式", "A2": "B2C铺货模式",
    "B1": "B2B现货批发", "B2": "B2B定制询盘",
    "C1": "海外一件代发", "C2": "海外零售商配送",
    "D1": "独立站短视频/直播", "D2": "独立站图文/搜索",
    "E1": "大客户工程/招投标", "E2": "大客户资质/认证",
    "F1": "蓄力学习中", "F2": "缺意愿/资质",
}
