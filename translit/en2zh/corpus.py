# -*- coding: utf-8 -*-
"""
基于真实译名语料的检索式音译。

思路：手里有上万条「英文人名 -> 官方中文译名」的平行数据
（Onomaverse 多语言译名数据集，CC BY 4.0）。把每个英文名转成
CMU 音素序列建索引；查询时把输入词也转成音素，在索引里找
发音最近的名字，直接借用它的官方译字。

这仍然是"发音匹配"，只是用字的参照从手写规则换成了上万条
真实译名；找不到足够近的才回退到规则引擎。
"""

import os
import csv
import re
import functools

from . import g2p

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_PATH = os.path.join(DATA_DIR, "names.csv")
INDEX_PATH = os.path.join(DATA_DIR, "translit_index.tsv")

_MIN_SIM = 0.80          # 音素相似度低于该值视为"没找到"
_HAN_RE = re.compile(r"^[\u4e00-\u9fff·\u2019' ]+$")


def _phon_key(phonemes) -> tuple:
    """去重音的音素元组，用于比对"""
    return tuple(p[:-1] if p and p[-1].isdigit() else p for p in phonemes)


@functools.lru_cache(maxsize=1)
def _load_index():
    """
    返回 [(phoneme_tuple, name_lower, zh), ...]（按长度排序，便于剪枝）。
    首次运行会从 names.csv 构建并缓存到 translit_index.tsv。
    """
    if os.path.exists(INDEX_PATH):
        entries = []
        with open(INDEX_PATH, encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3:
                    continue
                name, phons, zh = parts[:3]
                cnt = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1
                # 防御：无论索引里是否带重音数字，加载时统一去掉
                entries.append((_phon_key(phons.split()), name, zh, cnt))
        return entries

    if not os.path.exists(CSV_PATH):
        return []

    entries = {}
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lang = (row.get("lang_code") or "").lower()
            if lang.split("-")[0] != "zh":
                continue
            name = (row.get("name") or "").strip()
            zh = (row.get("localized_form") or "").strip()
            if not name or not zh:
                continue
            if not _HAN_RE.match(zh):
                continue          # 只要纯汉字音译（含·间隔号）
            name_l = name.lower()
            if name_l in entries:
                continue
            phons, source = g2p.word_to_phonemes(name_l)
            if source not in ("dict", "dict+affix"):
                continue          # 词典查不到的名字发音不可靠，不进索引
            entries[name_l] = (_phon_key(phons), name_l, zh)

    out = [(p, n, z) for n, (p, _, z) in entries.items()]
    out.sort(key=lambda e: len(e[0]))
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        for p, n, z in out:
            f.write(f"{n}\t{' '.join(p)}\t{z}\n")
    return out


def _edit_distance(a: tuple, b: tuple, cap: int) -> int:
    """音素序列编辑距离，超过 cap 提前放弃"""
    la, lb = len(a), len(b)
    if abs(la - lb) > cap:
        return cap + 1
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        lo = max(1, i - cap)
        hi = min(lb, i + cap)
        for j in range(1, min(hi, lb) + 1):
            if j < lo:
                cur[j] = cap + 1
                continue
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        for j in range(hi + 1, lb + 1):
            cur[j] = cap + 1
        prev = cur
    return prev[lb]


def search(word: str, top_k: int = 5):
    """
    在译名语料里找发音最接近的名字。
    返回 (zh, similarity, matched_name) 或 None。
    """
    entries = _load_index()
    if not entries:
        return None

    w = word.lower()
    phons, source = g2p.word_to_phonemes(w)
    if source not in ("dict", "dict+affix"):
        return None
    q = _phon_key(phons)
    n = len(q)
    best = []
    for p, name, zh, cnt in entries:
        if abs(len(p) - n) > 2:
            continue
        d = _edit_distance(q, p, cap=3)
        if d > 3:
            continue
        sim = 1.0 - d / max(n, len(p))
        best.append((sim, name, zh, cnt))
        if len(best) > 400:
            best.sort(key=lambda t: (t[0], t[1] == w), reverse=True)
            best = best[:50]
    if not best:
        return None
    # 同分时：拼写完全一致的名字优先（压过发音相同的拼错变体）
    best.sort(key=lambda t: (t[0], t[1] == w), reverse=True)
    top = best[:top_k]

    # 借用条件：音素序列完全一致（同音异拼才安全）。
    # 放宽过 0.8 会张冠李戴（party->马蒂[Marty]）；cnt>=2 门槛也试过，
    # 但小语料里 London/Washington 也只出现 1 次，会误伤大片正常命中。
    # 假音素（arely=are+ly 丢尾）才是垃圾命中的主因，已在索引构建侧排除。
    if top[0][0] >= 0.999:
        return top[0][2], top[0][0], top[0][1]
    return None


def stats():
    e = _load_index()
    return len(e)
