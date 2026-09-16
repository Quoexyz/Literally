# -*- coding: utf-8 -*-
"""音素序列 -> 音节切分。"""

from .arpabet import is_vowel, strip_stress, VALID_CC_ONSET


def syllabify(phons: list[str]) -> list[tuple[list[str], str, list[str]]]:
    """
    把带重音的 ARPABET 序列切成音节。
    返回 [(onset, nucleus, coda), ...]；无元音时返回 []。
    """
    v_idx = [i for i, p in enumerate(phons) if is_vowel(p)]
    if not v_idx:
        return []

    n_syl = len(v_idx)
    onsets: list[list[str]] = [[] for _ in range(n_syl)]
    codas: list[list[str]] = [[] for _ in range(n_syl)]

    onsets[0] = list(phons[: v_idx[0]])

    for k in range(n_syl - 1):
        mid = phons[v_idx[k] + 1: v_idx[k + 1]]
        n = len(mid)
        if n == 0:
            codas[k], onsets[k + 1] = [], []
        elif n == 1:
            codas[k], onsets[k + 1] = [], list(mid)
        elif n == 2:
            pair = "".join(strip_stress(c) for c in mid)
            if pair in VALID_CC_ONSET:
                codas[k], onsets[k + 1] = [], list(mid)
            else:
                codas[k], onsets[k + 1] = [mid[0]], [mid[1]]
        else:
            # 3 个及以上：第一个归前韵尾，其余归后（若后两个是合法 onset）
            if "".join(strip_stress(c) for c in mid[1:3]) in VALID_CC_ONSET and n == 3:
                codas[k], onsets[k + 1] = [mid[0]], list(mid[1:])
            else:
                codas[k], onsets[k + 1] = [mid[0]], list(mid[1:])

    codas[-1] = list(phons[v_idx[-1] + 1:])

    # 修正：NG 不能作音节首（singer = sing·er）
    for k in range(1, n_syl):
        while onsets[k] and strip_stress(onsets[k][0]) == "NG":
            codas[k - 1].append(onsets[k].pop(0))

    # 修正：音节首最多 3 个辅音
    for k in range(n_syl):
        while len(onsets[k]) > 3:
            if k == 0:
                break
            codas[k - 1].insert(0, onsets[k].pop(0))

    return [(onsets[k], phons[v_idx[k]], codas[k]) for k in range(n_syl)]
