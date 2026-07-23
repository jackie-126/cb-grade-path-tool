import re
import unicodedata


FULLWIDTH_MAP = {
    "Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D", "Ｅ": "E", "Ｆ": "F",
    "Ｇ": "G", "Ｈ": "H", "Ｉ": "I", "Ｊ": "J", "Ｋ": "K", "Ｌ": "L",
    "Ｍ": "M", "Ｎ": "N", "Ｏ": "O", "Ｐ": "P", "Ｑ": "Q", "Ｒ": "R",
    "Ｓ": "S", "Ｔ": "T", "Ｕ": "U", "Ｖ": "V", "Ｗ": "W", "Ｘ": "X",
    "Ｙ": "Y", "Ｚ": "Z",
    "ａ": "a", "ｂ": "b", "ｃ": "c", "ｄ": "d", "ｅ": "e", "ｆ": "f",
    "ｇ": "g", "ｈ": "h", "ｉ": "i", "ｊ": "j", "ｋ": "k", "ｌ": "l",
    "ｍ": "m", "ｎ": "n", "ｏ": "o", "ｐ": "p", "ｑ": "q", "ｒ": "r",
    "ｓ": "s", "ｔ": "t", "ｕ": "u", "ｖ": "v", "ｗ": "w", "ｘ": "x",
    "ｙ": "y", "ｚ": "z",
    "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
    "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
    "（": "(", "）": ")", "【": "[", "】": "]", "：": ":", "；": ";",
    "，": ",", "。": ".", "、": ",", "～": "~", "—": "-", "–": "-",
    "％": "%", "＋": "+", "＝": "=", "　": " ",
    "～": "~", "〜": "~", ",": ",", "，": ",",
}

YES_NO_MAP = {
    "是": "是", "有": "是", "yes": "是", "y": "是", "true": "是", "1": "是",
    "ＹＥＳ": "是", "ｔｒｕｅ": "是",
    "否": "否", "无": "否", "没有": "否", "no": "否", "n": "否", "false": "否", "0": "否",
    "ＮＯ": "否", "ｆａｌｓｅ": "否",
}

CONNECTOR_MAP = {
    "—": "-", "–": "-", "─": "-", "━": "-", "ー": "-",
    "～": "~", "〜": "~", "～": "~",
}


def normalize(s):
    if s is None:
        return ""
    text = str(s).strip()

    result = []
    for ch in text:
        if ch in FULLWIDTH_MAP:
            result.append(FULLWIDTH_MAP[ch])
        else:
            result.append(ch)
    text = "".join(result)

    for ch, repl in CONNECTOR_MAP.items():
        text = text.replace(ch, repl)

    text = text.replace(",", "").replace("/", "")

    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_yes_no(s):
    n = normalize(s).lower().strip()
    return YES_NO_MAP.get(n, n)


def normalize_number(s):
    n = normalize(s)
    n = n.replace(",", "").replace("，", "")
    n = re.sub(r"[^\d.\-]", "", n)
    try:
        return float(n) if n else 0
    except ValueError:
        return 0


def normalize_sku(s):
    n = normalize(s)
    n = n.replace("个", "").replace("以上", "").replace("以下", "").strip()
    if "~" in n:
        parts = n.split("~")
        try:
            return int(parts[0].strip())
        except ValueError:
            return 0
    if "-" in n:
        parts = n.split("-")
        try:
            return int(parts[0].strip())
        except ValueError:
            return 0
    try:
        return int(n)
    except ValueError:
        return 0


def normalize_moq(s):
    n = normalize(s)
    n = n.replace("元", "").replace(",", "").replace("，", "").strip()
    if "~" in n:
        parts = n.split("~")
        try:
            return int(parts[0].strip())
        except ValueError:
            return 999999
    if "-" in n and not n.replace("-", "").replace(".", "").isdigit():
        parts = n.split("-")
        try:
            return int(parts[0].strip())
        except ValueError:
            return 999999
    try:
        return int(re.sub(r"[^\d]", "", n))
    except ValueError:
        return 999999


def normalize_percent(s):
    n = normalize(s)
    if "不清楚" in n or "无" in n:
        return 0
    n = n.replace("%", "").replace("％", "").strip()
    n = n.replace("及以上", "").replace("以下", "").replace("/无预留", "").strip()
    if "~" in n:
        parts = n.split("~")
        try:
            return float(parts[0].strip())
        except ValueError:
            return 0
    if "-" in n:
        parts = n.split("-")
        try:
            return float(parts[0].strip())
        except ValueError:
            return 0
    try:
        return float(n)
    except ValueError:
        return 0


def normalize_count(s):
    n = normalize(s)
    if n in ["否", "不参加", "无", "0", "不适用"]:
        return 0
    digits = re.sub(r"[^\d]", "", n)
    try:
        return int(digits) if digits else 0
    except ValueError:
        return 0
