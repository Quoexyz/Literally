# -*- coding: utf-8 -*-
"""
英文单词 -> ARPABET 音素序列。

主路径：查 CMU 发音词典（13 万词条，覆盖绝大多数英文单词与常见专名）。
回退路径：
  1. 形态还原（cats -> cat, played -> play, running -> run）
  2. 拼写规则 G2P（覆盖 CMUdict 未收录的生僻专名 / 造词）
"""

import os
import re
import functools

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CMU_PATH = os.path.join(DATA_DIR, "cmudict.dict")

_STRESS_RE = re.compile(r"\d")


@functools.lru_cache(maxsize=1)
def load_cmudict() -> dict[str, list[str]]:
    """加载 CMUdict，返回 {word: [PHONEMES...]}"""
    d: dict[str, list[str]] = {}
    if not os.path.exists(CMU_PATH):
        return d
    with open(CMU_PATH, encoding="latin-1") as f:
        for line in f:
            if line.startswith(";;;") or not line.strip():
                continue
            # cmudict 不同发行版用 1~2 个空格分隔，按首个空白串切分最稳妥
            parts = re.split(r"\s+", line.strip(), maxsplit=1)
            if len(parts) != 2:
                continue
            word, phons = parts[0].strip(), parts[1].strip()
            # 去掉变体后缀 WORD(1) WORD(2)，只保留主条目
            if word.endswith(")") and "(" in word:
                base, _, num = word[:-1].rpartition("(")
                if num == "1":
                    word = base
                else:
                    continue
            word = word.lower()
            if word not in d:
                d[word] = phons.split()
    return d


# ---------------------------------------------------------------------------
# 形态还原：词典查不到时，尝试还原词干再查
# ---------------------------------------------------------------------------
def _stem_variants(word: str) -> list[str]:
    w = word.lower()
    cands = []
    if w.endswith("'s"):
        cands.append(w[:-2])
    if w.endswith("ies") and len(w) > 4:
        cands.append(w[:-3] + "y")
    if w.endswith("es") and len(w) > 3:
        cands.append(w[:-2])
        cands.append(w[:-1])
    if w.endswith("s") and len(w) > 2 and not w.endswith("ss"):
        cands.append(w[:-1])
    if w.endswith("ed") and len(w) > 3:
        cands.append(w[:-2])
        cands.append(w[:-1])
        if len(w) > 4 and w[-3] == w[-4]:
            cands.append(w[:-3])
    if w.endswith("ing") and len(w) > 4:
        cands.append(w[:-3])
        cands.append(w[:-3] + "e")
        if len(w) > 5 and w[-4] == w[-5]:
            cands.append(w[:-4])
    if w.endswith("ly") and len(w) > 3:
        cands.append(w[:-2])
    if w.endswith("est") and len(w) > 4:
        cands.append(w[:-3])
        cands.append(w[:-2])
    if w.endswith("er") and len(w) > 3:
        cands.append(w[:-2])
        cands.append(w[:-1])
    return cands


def _plural_s_phon(last: str) -> str:
    """/s/ /z/ /ɪz/ 的选择"""
    if last in ("S", "Z", "SH", "ZH", "CH", "JH"):
        return "AH0 Z"
    if last in ("P", "T", "K", "F", "TH"):
        return "S"
    return "Z"


# ---------------------------------------------------------------------------
# 拼写规则 G2P（回退用）
# ---------------------------------------------------------------------------
# 顺序敏感：长组合在前
RULES = [
    (r"TION", "SH AH N"), (r"SION", "ZH AH N"), (r"CIAL", "SH AH L"),
    (r"TIAN", "SH AH N"), (r"CIAN", "SH AH N"), (r"TIAL", "SH AH L"),
    (r"OUGH", "AH F"), (r"AUGH", "AO F"), (r"EIGH", "EY"),
    (r"IGH", "AY"), (r"IGN$", "AY N"), (r"IGN", "IH G N"),
    (r"CH", "CH"), (r"SH", "SH"), (r"TH", "TH"), (r"PH", "F"),
    (r"WH", "W"), (r"CK", "K"), (r"NG", "NG"), (r"QU", "K W"),
    (r"EE", "IY"), (r"EA", "IY"), (r"EI", "EY"), (r"IE", "IY"),
    (r"OO", "UW"), (r"OU", "AW"), (r"OW$", "OW"), (r"OW", "AW"),
    (r"OI", "OY"), (r"OY", "OY"), (r"AI", "EY"), (r"AY", "EY"),
    (r"AU", "AO"), (r"AW", "AO"), (r"EW", "UW"), (r"UE", "UW"),
    (r"EY$", "IY"), (r"OE", "OW"), (r"OA", "OW"),
    # 单字母
    (r"A", "AE"), (r"B", "B"), (r"C", "K"), (r"D", "D"), (r"E", "EH"),
    (r"F", "F"), (r"G", "G"), (r"H", "HH"), (r"I", "IH"), (r"J", "JH"),
    (r"K", "K"), (r"L", "L"), (r"M", "M"), (r"N", "N"), (r"O", "AA"),
    (r"P", "P"), (r"R", "R"), (r"S", "S"), (r"T", "T"), (r"U", "AH"),
    (r"V", "V"), (r"W", "W"), (r"X", "K S"), (r"Y", "Y"), (r"Z", "Z"),
]
_RULES = [(re.compile(p), o) for p, o in RULES]


def _rule_g2p(word: str) -> list[str]:
    """基于拼写规则的朴素 G2P，仅用于词典未收录的词。"""
    w = word.upper()
    # 词尾静音 e
    silent_e = w.endswith("E") and len(w) > 2 and w[-2] not in "AEIOUY"
    if silent_e:
        w = w[:-1]

    out: list[str] = []
    i = 0
    n = len(w)
    while i < n:
        matched = False
        for rx, phons in _RULES:
            m = rx.match(w, i)
            if m and m.end() > i:
                out.extend(phons.split())
                i = m.end()
                matched = True
                break
        if not matched:
            i += 1
    if not out:
        out = ["AH0"]
    # 加主重音：默认落在第一个元音上
    marked = []
    done = False
    for p in out:
        if not done and p in ("AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER",
                              "EY", "IH", "IY", "OW", "OY", "UH", "UW"):
            marked.append(p + "1")
            done = True
        elif p in ("AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER",
                   "EY", "IH", "IY", "OW", "OY", "UH", "UW"):
            marked.append(p + "0")
        else:
            marked.append(p)
    return marked


def word_to_phonemes(word: str) -> tuple[list[str], str]:
    """
    返回 (音素列表, 来源)。
    来源: 'dict' | 'dict+affix' | 'rule'
    """
    d = load_cmudict()
    w = word.lower()
    if w in d:
        return list(d[w]), "dict"

    # 全大写缩写（USA / IBM / NASA）：CMUdict 里可能以点分形式收录
    if w.isupper() and len(w) <= 6:
        for variant in (w, ".".join(w) + "."):
            if variant.lower() in d:
                return list(d[variant.lower()]), "dict"

    # 形态还原
    for stem in _stem_variants(w):
        if stem in d:
            base = list(d[stem])
            tail = w[len(stem):] if w.startswith(stem) else ""
            if tail == "s":
                last = _strip_stress(base[-1])
                base += _plural_s_phon(last).split()
            elif tail == "d" or tail == "ed":
                last = _strip_stress(base[-1])
                if last in ("T", "D"):
                    base.append("AH0 D")
                    base[-1] = "IH0 D"
                elif last in ("P", "K", "F", "TH", "CH", "SH", "S"):
                    base.append("T")
                else:
                    base.append("D")
            elif tail == "ing":
                pass
            return base, "dict+affix"
    return _rule_g2p(word), "rule"


def _strip_stress(p: str) -> str:
    return p[:-1] if p and p[-1].isdigit() else p
