# -*- coding: utf-8 -*-
"""英文 -> 中文音译主逻辑。"""

import re

from . import g2p
from . import arpabet as ab
from . import lexicon
from . import corpus
from .syllabify import syllabify

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*")


def _piece_to_zh(phons: list[str]) -> str:
    """一段音素 -> 汉字串"""
    syls = syllabify(phons)
    if not syls:
        return ""
    out: list[str] = []
    for i, (onset, nucleus, coda) in enumerate(syls):
        stressed = ab.stress_of(nucleus) >= 1
        is_last = (i == len(syls) - 1)
        for key, zh in ab.syllable_to_zh(onset, nucleus, coda, stressed, is_last,
                                         is_first=(i == 0)):
            if key.startswith(("SCHWA:", "UFORM:")) or key in ("NIU", "HIU", "SSH"):
                zh = ab.schwa_char(key)
            if zh:
                out.append(zh)
    return "".join(out)


def transliterate_word(word: str, with_detail: bool = False):
    """
    单词 -> 中文音译。
    with_detail=True 时返回 dict（含音素、音节、来源）。
    """
    raw = word
    w = word.lower().strip()
    w = w.replace("’", "'")
    if not w:
        return ({"zh": "", "source": "empty"} if with_detail else "")

    # 1. 译名表（官方/约定俗成译法优先）
    hit = lexicon.lookup(w)
    if hit:
        if with_detail:
            return {"zh": hit, "source": "lexicon", "phonemes": [], "syllables": [],
                    "word": raw}
        return hit

    # 1b. 真实译名语料检索：发音最近的名字直接借用其官方译字
    found = corpus.search(w)
    if found:
        zh, sim, matched = found
        if with_detail:
            phons, _ = g2p.word_to_phonemes(w)
            return {"zh": zh, "source": f"corpus({matched},{sim:.2f})",
                    "phonemes": phons, "syllables": [], "word": raw}
        return zh

    # 2. 属格 's 在音译中弱读，直接忽略（Court's -> Court -> 科尔特）
    if w.endswith("'s") and len(w) > 2:
        return transliterate_word(w[:-2], with_detail=with_detail)

    # 3. 带连字符的复合词：分段处理
    if "-" in w:
        parts = [p for p in w.split("-") if p]
        if len(parts) > 1:
            zhs = [transliterate_word(p) for p in parts]
            res = "".join(zhs)
            if with_detail:
                return {"zh": res, "source": "compound", "phonemes": [], "syllables": [],
                        "word": raw}
            return res

    # 3. G2P + 音译
    phons, source = g2p.word_to_phonemes(w)
    zh = _piece_to_zh(phons)

    if with_detail:
        syls = syllabify(phons)
        return {
            "zh": zh,
            "source": source,
            "phonemes": phons,
            "syllables": [
                {
                    "onset": s[0], "nucleus": s[1], "coda": s[2],
                    "zh": "".join(
                        ab.schwa_char(k) if k.startswith(("SCHWA:", "UFORM:")) or k in ("NIU", "HIU") else z
                        for k, z in ab.syllable_to_zh(s[0], s[1], s[2],
                                                      ab.stress_of(s[1]) >= 1,
                                                      i == len(syls) - 1,
                                                      is_first=(i == 0))
                    ),
                }
                for i, s in enumerate(syls)
            ],
            "word": raw,
        }
    return zh


def transliterate(text: str, with_detail: bool = False) -> str:
    """整段文本 -> 音译（保留标点、数字、其他字符）"""

    def repl(m: re.Match) -> str:
        r = transliterate_word(m.group(0), with_detail=with_detail)
        return r["zh"] if with_detail else r

    return _WORD_RE.sub(repl, text)


def analyze(text: str) -> list[dict]:
    """返回逐词详情，供 UI 展示"""
    out = []
    for m in _WORD_RE.finditer(text):
        d = transliterate_word(m.group(0), with_detail=True)
        d["offset"] = m.start()
        out.append(d)
    return out
