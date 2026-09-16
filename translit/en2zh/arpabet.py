# -*- coding: utf-8 -*-
"""
ARPABET 音素 -> 汉语拼音 / 汉字 的映射规则。

ARPABET 是 CMU 发音词典使用的音标体系。本模块负责把英语音素转换成
"声母 + 韵母"的汉语近似，再交给 pinyin_map 取字。

设计要点：
  1. 英语 R 在音节首按汉语 l 处理（里/拉/洛），这是中文译名的主流做法
     （Green=格林、Brown=布朗、Robert=罗伯特）；R 在音节尾作"尔"。
  2. 鼻音韵尾 -n/-ng 与元音合并成一个汉字（班/金/宋），而不是"巴+恩"。
  3. -m 在音节末单独成"姆"（Tom=塔姆）；-m 后还有辅音时脱落（lamp=兰普）。
  4. 重读元音用响亮字（a/ai/ao），非重读用轻字（e/er）。
"""

from . import pinyin_map as pm

# ---------------------------------------------------------------------------
VOWELS = {
    "AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER",
    "EY", "IH", "IY", "OW", "OY", "UH", "UW",
}
CONSONANTS = {
    "B", "CH", "D", "DH", "F", "G", "HH", "JH", "K", "L", "M",
    "N", "NG", "P", "R", "S", "SH", "T", "TH", "V", "W", "Y", "Z", "ZH",
}

# ---------------------------------------------------------------------------
# 辅音 -> 拼音声母（作音节首）
# ---------------------------------------------------------------------------
ONSET2PY = {
    "B": "b", "P": "p", "M": "m", "F": "f",
    "D": "d", "T": "t", "N": "n", "L": "l",
    "G": "g", "K": "k", "HH": "h",
    "JH": "j", "CH": "ch", "SH": "sh",
    "R": "l",          # 英语 /r/ -> 汉语 l（里/拉/洛）
    "S": "s", "Z": "z",
    "TH": "s",         # /θ/
    "DH": "z",         # /ð/
    "V": "w", "W": "w", "Y": "y",
    "ZH": "zh",
}

# ---------------------------------------------------------------------------
# 元音 -> 拼音韵母
#   (重读形式, 非重读形式)
# ---------------------------------------------------------------------------
VOWEL2FINAL = {
    "AA": ("a", "a"),
    "AE": ("a", "a"),
    "AH": ("a", "e"),     # 重读 /ʌ/ -> a（cup=卡普）；非重读 schwa -> e
    "AO": ("ao", "ao"),
    "AW": ("ao", "ao"),
    "AY": ("ai", "ai"),
    "EH": ("e", "e"),
    "ER": ("er", "er"),
    "EY": ("ei", "i"),    # 词尾非重读 -ay/-ey -> i（Sunday=森迪）
    "IH": ("i", "i"),
    "IY": ("i", "i"),
    "OW": ("ou", "ou"),
    "OY": ("oy", "oy"),
    "UH": ("u", "u"),
    "UW": ("u", "u"),
}

# ---------------------------------------------------------------------------
# 元音 + 鼻音韵尾 -> 鼻化韵母（合并成一个汉字）
# ---------------------------------------------------------------------------
NASAL_FINAL = {
    # -n
    ("AA", "N"): ("an", "an"),
    ("AE", "N"): ("an", "an"),
    ("AH", "N"): ("an", "en"),
    ("EH", "N"): ("en", "en"),
    ("ER", "N"): ("en", "en"),
    ("EY", "N"): ("en", "en"),
    ("IH", "N"): ("in", "in"),
    ("IY", "N"): ("in", "in"),
    ("AO", "N"): ("ang", "ang"),
    ("OW", "N"): ("ong", "ong"),
    ("AW", "N"): ("ang", "ang"),
    ("AY", "N"): ("an", "an"),
    ("UH", "N"): ("un", "un"),
    ("UW", "N"): ("un", "un"),
    ("OY", "N"): ("ong", "ong"),
    # -ng
    ("AA", "NG"): ("ang", "ang"),
    ("AE", "NG"): ("ang", "ang"),
    ("AH", "NG"): ("ang", "eng"),
    ("EH", "NG"): ("eng", "eng"),
    ("ER", "NG"): ("eng", "eng"),
    ("EY", "NG"): ("eng", "eng"),
    ("IH", "NG"): ("ing", "ing"),
    ("IY", "NG"): ("ing", "ing"),
    ("AO", "NG"): ("ong", "ong"),
    ("OW", "NG"): ("ong", "ong"),
    ("AW", "NG"): ("ang", "ang"),
    ("AY", "NG"): ("ang", "ang"),
    ("UH", "NG"): ("ong", "ong"),
    ("UW", "NG"): ("ong", "ong"),
    ("OY", "NG"): ("ong", "ong"),
}

# ---------------------------------------------------------------------------
# 音节尾辅音 -> 汉字（用于非鼻音韵尾）
# ---------------------------------------------------------------------------
CODA2ZH = {
    "L": "尔",   # dark l：ball=鲍尔
    "R": "尔",
    "M": "姆",
    "S": "斯",
    "Z": "斯",   # 词尾 /z/ 译"斯"：Charles=查尔斯、James=詹姆斯
    "T": "特",
    "D": "德",
    "K": "克",
    "F": "夫",
    "V": "夫",
    "P": "普",
    "B": "布",
    "G": "格",
    "CH": "尺",   # 音节尾 /tʃ/：each=伊尺（比"奇"更贴听感）
    "JH": "尺",
    "SH": "什",
    "ZH": "日",
    "TH": "斯",
    "DH": "兹",
    "HH": "赫",
    "N": "恩",    # 兜底：通常已被鼻化处理
    "NG": "恩",
}

# ---------------------------------------------------------------------------
# 辅音簇中"落单"的辅音 -> 单元音化汉字（schwa 化）
# 例如 Brown = B(布) + R+AW+N(朗) = 布朗
# ---------------------------------------------------------------------------
SCHWA_ZH = {
    "B": "布", "P": "普", "D": "德", "T": "特", "G": "格", "K": "克",
    "F": "弗", "V": "弗", "M": "姆", "N": "恩", "L": "勒", "R": "尔",
    "S": "斯", "Z": "兹", "SH": "什", "ZH": "日", "CH": "奇", "JH": "吉",
    "TH": "斯", "DH": "德", "HH": "赫", "W": "伍", "Y": "伊", "NG": "恩",
}

# ---------------------------------------------------------------------------
# 允许出现在音节首的二合辅音（用于音节切分）
# ---------------------------------------------------------------------------
VALID_CC_ONSET = {
    "PL", "PR", "BL", "BR", "TR", "TW", "DR", "DW", "KL", "KR", "KW",
    "GL", "GR", "GW", "FL", "FR", "THR", "THW", "SHR", "SL", "SW",
    "SP", "ST", "SK", "SM", "SN", "SQ", "SPR", "STR", "SKR", "SKW",
    "SPL", "SHL", "VL", "VR", "MR", "ML",
}


def strip_stress(ph: str) -> str:
    """去掉重音数字：AH1 -> AH"""
    return ph[:-1] if ph and ph[-1].isdigit() else ph


def stress_of(ph: str) -> int:
    """取重音等级：主重音 1、次重音 2、无重音 0"""
    if ph and ph[-1].isdigit():
        return int(ph[-1])
    return 0


def is_vowel(ph: str) -> bool:
    return strip_stress(ph) in VOWELS


def onset_initial(ph: str) -> str:
    """辅音 -> 拼音声母；不是辅音返回空串"""
    return ONSET2PY.get(strip_stress(ph), "")


# ---------------------------------------------------------------------------
# 核心：把一个音节（onset + nucleus + coda）转成汉字片段
# ---------------------------------------------------------------------------
def syllable_to_zh(onset: list[str], nucleus: str, coda: list[str],
                   stressed: bool, is_last: bool,
                   is_first: bool = False) -> list[tuple[str, str]]:
    """
    返回 [(拼音或标记, 汉字), ...]，一个音节可能产生 1~N 个汉字。

    onset   : 音节首辅音列表
    nucleus : 元音（带重音数字）
    coda    : 音节尾辅音列表
    stressed: 是否重读
    is_last : 是否是词的最后一个音节
    is_first: 是否是词的第一个音节（词首 s+辅音 译"史"）
    """
    out: list[tuple[str, str]] = []
    v = strip_stress(nucleus)

    # 韵尾清洗：/r/ 后的 /l/ 脱落（Charles=查尔斯，而非"查尔尔兹"）
    coda = [c for i, c in enumerate(coda)
            if not (strip_stress(c) == "L" and i > 0 and strip_stress(coda[i - 1]) == "R")]

    # --- 1. 辅音簇：除最后一个辅音外，前面的都单元音化成独立音节 ---
    #     street = S(斯) + T(特) + R+IY(里) + T(特) = 斯特里特
    initial = ""
    main_c = ""
    yiu = None
    if onset:
        onset2 = _fix_glide_cluster(onset, v)
        for c in onset2[:-1]:
            out.append((f"SCHWA:{c}", SCHWA_ZH.get(strip_stress(c), "")))
        tail = onset2[-1]
        if tail.startswith("YIU:"):
            yiu = tail.split(":", 1)[1]
        elif tail.startswith("UFORM:"):
            out.append((tail, tail.split(":", 1)[1]))
        elif tail in ("NIU", "HIU"):
            out.append((tail, schwa_char(tail)))
        else:
            initial = onset_initial(tail)
            main_c = strip_stress(tail)

    # /Cjuː/：C+i 字 + 尤（beautiful=比尤…、cute=基尤特）
    if yiu is not None:
        base = ONSET2PY.get(yiu, "")
        res = pm.resolve(base, "i") if base else ("i", pm.PY2ZH["i"])
        if res:
            out.append(res)
        out.append(("iu", "尤"))
        _append_coda(out, coda, v)
        return [x for x in out if x[1]]

    # --- 2. 鼻音韵尾：元音 + n/ng 合并成一个汉字 ---
    nasal = None
    rest_coda = list(coda)
    if rest_coda and strip_stress(rest_coda[0]) in ("N", "NG"):
        nasal = strip_stress(rest_coda[0])
        rest_coda = rest_coda[1:]

    idx = 0 if stressed else 1
    # 非重读 AH 在词尾音节 -> e；在词中 -> a（banana 巴纳纳 / London 兰登）
    if v == "AH" and not stressed and not is_last:
        idx = 0

    if nasal and (v, nasal) in NASAL_FINAL:
        final = NASAL_FINAL[(v, nasal)][idx]
    elif v == "OY":
        # /ɔɪ/ 拆成"奥伊"两个字：boy=鲍伊、Roy=罗伊
        res = pm.resolve(initial, "ao") if initial else None
        if res:
            out.append(res)
        else:
            out.append(("ao", pm.PY2ZH["ao"]))
        out.append(("i", pm.PY2ZH["i"]))
        _append_coda(out, rest_coda, v)
        return [x for x in out if x[1]]
    else:
        final = VOWEL2FINAL.get(v, ("a", "e"))[idx]

    # 英语 /r/ 的映射：
    #   - R 在 i 前一律用 r 系字（听感是"瑞"）：recent=瑞森特、Supreme=苏普瑞姆、
    #     read=瑞德；鼻化时仍自然落到"林"（Green=格林）
    #   - 词首单独的 R：EY/EH 前用"雷"（Ray=雷、red=雷德），AY 前用"瑞"（Ryan=瑞安）
    #   - R 在后元音（a/o/u 类）前用"罗"：Robert=罗伯特、Rose=罗斯
    #   - 其余位置用 l 系：run=兰、around=阿朗德
    if main_c == "R":
        r_alone = len(onset) == 1 and strip_stress(onset[0]) == "R"
        if v in ("IY", "IH"):
            initial = "r"                 # ri -> 瑞
        elif r_alone and v == "AY":
            initial, final = "r", "ui"    # Rice=瑞斯、Ryan=瑞安
        elif r_alone and v in ("EH", "EY"):
            final = "ei"                  # red=雷德、Ray=雷
        elif v in ("AA", "AO", "OW") and nasal is None:
            final = "uo"                  # Robert=罗伯特、Rose=罗斯、Roger=罗杰

    # /tʃ/、/ʃ/ 在前元音前颚化：check=切克、chip=奇普、shell=谢尔
    if nasal is None:
        if main_c == "CH" and v in ("EH", "IH", "IY"):
            initial = "q"
        elif main_c == "SH" and v == "EH":
            initial = "x"

    # /dʒ/ 在中央元音 /ɜːr/ 前更贴 zh：journey=哲尔尼（而非"杰尔尼"）
    if main_c == "JH" and v == "ER" and nasal is None:
        initial = "zh"

    # --- 3. ER 特殊 ---
    if v == "ER" and nasal is None and not rest_coda:
        # 词尾非重读的 -er/-or 直接用一个字：water=瓦特、teacher=蒂切、mother=马泽
        if is_last and not stressed and initial:
            res = pm.resolve(initial, "er")
            if res and res[0] == initial + "er":
                out.append(res)
                return [x for x in out if x[1]]
        # 重读音节补"尔"：her=赫尔
        res = pm.resolve(initial, "e") if initial else ("e", pm.PY2ZH["e"])
        if res:
            out.append(res)
        out.append(("er", "尔"))
        return [x for x in out if x[1]]

    # --- 4. 声母 + 韵母 -> 汉字 ---
    res = pm.resolve(initial, final) if initial else _final_to_zh(final)
    if res is None:
        res = _final_to_zh(final)
    if res:
        out.append(res)

    # --- 5. -m：在音节末译"姆"（Tom=塔姆）；后面还有辅音则脱落（lamp=兰普） ---
    if rest_coda and strip_stress(rest_coda[-1]) == "M":
        out.append(("m", "姆"))
    rest_coda = [c for c in rest_coda if strip_stress(c) != "M"]

    _append_coda(out, rest_coda, v)
    return [x for x in out if x[1]]


def _final_to_zh(final: str) -> tuple[str, str] | None:
    """零声母：韵母 -> 汉字"""
    if final in pm.PY2ZH:
        return final, pm.PY2ZH[final]
    for simpler in pm._FALLBACK_FINALS.get(final, [final]):
        if simpler in pm.PY2ZH:
            return simpler, pm.PY2ZH[simpler]
    return None


def _append_coda(out: list[tuple[str, str]], coda: list[str], v: str) -> None:
    """把剩余韵尾辅音逐个转成汉字"""
    for c in coda:
        c = strip_stress(c)
        if c in CODA2ZH:
            out.append((f"CODA:{c}", CODA2ZH[c]))


def _fix_glide_cluster(onset: list[str], vowel: str) -> list[str]:
    """
    处理 W / Y 位于辅音簇末尾的情况：
      K+W -> 库(省略 W)，T+Y -> 图，N+Y -> 纽
    """
    if len(onset) < 2:
        return onset
    last = strip_stress(onset[-1])
    prev = strip_stress(onset[-2])

    if last == "W":
        # KW/GW/SW/THW/FW：前一个辅音用 u 化字，W 省略（quick=库伊克、swim=苏因）
        # TW/DW 不在此列：twenty=特文蒂、dwell=德韦尔
        u_form = {"K": "库", "G": "古"}
        if prev in u_form:
            return onset[:-2] + [f"UFORM:{u_form[prev]}"]
    if last == "Y":
        # /Cjuː/ 在汉语里对应 C+i + "尤"：beautiful=比尤塔法尔、cute=基尤特
        if vowel == "UW":
            if prev == "N":
                return onset[:-2] + ["NIU"]
            if prev == "H":
                return onset[:-2] + ["HIU"]
            return onset[:-2] + [f"YIU:{prev}"]
        return onset[:-1]
    return onset


def schwa_char(token: str) -> str:
    """从 SCHWA:/UFORM: 标记中取出汉字"""
    if token == "SSH":
        return "史"
    if token.startswith("SCHWA:"):
        return SCHWA_ZH.get(token.split(":", 1)[1], "")
    if token.startswith("UFORM:"):
        return token.split(":", 1)[1]
    if token == "NIU":
        return "纽"
    if token == "HIU":
        return "休"
    return ""
