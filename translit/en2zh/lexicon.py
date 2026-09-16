# -*- coding: utf-8 -*-
"""
不规则译名的兜底表（默认留空）。

本翻译器以"发音匹配"为唯一驱动：英文 -> CMUdict 音素 -> 汉语音译。
此表只用于极少数发音与既定译法完全脱节的词（如 John=约翰），
默认清空；需要时可用 add() 或直接在下方字典里追加。
"""

LEXICON: dict[str, str] = {}


def lookup(word: str) -> str | None:
    return LEXICON.get(word)


def add(word: str, zh: str) -> None:
    LEXICON[word.lower()] = zh
