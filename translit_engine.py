# -*- coding: utf-8 -*-
"""
发音模仿（音译）引擎。

优先级：lexicon.json（手工词表） -> model.onnx（seq2seq 音译模型） -> 规则引擎兜底。
g2p / 规则引擎来自 en2zh 包（本目录），onnxruntime 仅在模型首次使用时加载。
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_DIR = os.path.join(_HERE, "translit")
for _p in (_HERE, _PKG_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from en2zh import g2p
from en2zh.transliterate import transliterate as _rule_translate

LEXICON_PATH = os.path.join(_PKG_DIR, "lexicon.json")
ONNX_PATH = os.path.join(_PKG_DIR, "model.onnx")
VOCAB_PATH = os.path.join(_PKG_DIR, "model_vocab.json")

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*")

_lexicon = None
_ort_session = None
_p2i = _i2c = _spec = None


def _load_lexicon():
    global _lexicon
    if _lexicon is None:
        try:
            with open(LEXICON_PATH, encoding="utf-8") as f:
                _lexicon = json.load(f)
        except Exception as e:
            print("[translit] lexicon load failed:", e)
            _lexicon = {}
    return _lexicon


def _load_onnx():
    """惰性加载 ONNX 模型；失败返回 False（后续词全部走规则兜底）。"""
    global _ort_session, _p2i, _i2c, _spec
    if _ort_session is False:
        return False          # 之前加载失败过，不再重试
    if _ort_session is not None:
        return True           # 已加载
    try:
        import onnxruntime as ort
        import numpy as np

        v = json.load(open(VOCAB_PATH, encoding="utf-8"))
        pad, bos, eos, unk = v["PAD"], v["BOS"], v["EOS"], v["UNK"]
        _spec = {"pad": pad, "bos": bos, "eos": eos, "unk": unk}
        _p2i = {p: i for i, p in enumerate([pad, unk] + v["phon_vocab"])}
        # 汉字侧布局固定：0=pad 1=bos 2=eos 3=unk，随后是 char_vocab
        _c2i = {c: i for i, c in enumerate([pad, bos, eos, unk] + v["char_vocab"])}
        _i2c = {i: c for c, i in _c2i.items()}
        _spec["bos_id"] = _c2i[bos]
        _spec["eos_id"] = _c2i[eos]
        providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
        _ort_session = ort.InferenceSession(ONNX_PATH, providers=providers)
        return True
    except Exception as e:
        print("[translit] onnx load failed, falling back to rules:", e)
        _ort_session = False
        return False


def _greedy_onnx(phons, maxlen=14):
    import numpy as np

    src = np.array([[_p2i.get(p, _p2i[_spec["unk"]]) for p in phons]], dtype=np.int64)
    cur = [_spec["bos_id"]]
    for _ in range(maxlen):
        logits = _ort_session.run(
            ["logits"],
            {"src": src, "tgt_in": np.array([cur], dtype=np.int64)},
        )[0]
        nxt = int(logits[0, -1].argmax())
        if nxt == _spec["eos_id"]:
            break
        cur.append(nxt)
    special = (0, 3, _spec["bos_id"], _spec["eos_id"])  # pad/unk/bos/eos
    return "".join(_i2c[i] for i in cur[1:] if i not in special)


def word_transliterate(word: str) -> tuple[str, str]:
    """单词音译，返回 (结果, 来源)。来源: lexicon | onnx | rule"""
    w = word.lower().replace("’", "'")
    # 1. 手工词表
    lex = _load_lexicon()
    if w in lex:
        return lex[w], "lexicon"
    # 复合词整体查不到时，逐段再查一次词表
    if "-" in w or "'" in w:
        parts = [p for p in re.split(r"[-']", w) if p]
        if len(parts) > 1 and all(p in lex for p in parts):
            if w.endswith("'s") and parts[-1] == "s":
                return "".join(lex[p] for p in parts[:-1]), "lexicon"
            return "".join(lex[p] for p in parts), "lexicon"

    # 2. ONNX 模型（需要词典原生发音）
    if _load_onnx():
        phons, src = g2p.word_to_phonemes(w)
        if src == "dict":
            try:
                return _greedy_onnx(phons), "onnx"
            except Exception as e:
                print("[translit] onnx inference failed:", e)

    # 3. 规则引擎兜底
    return _rule_translate(word), "rule"


def transliterate(text: str) -> tuple[str, list[str]]:
    """
    整句音译。返回 (结果文本, 各词来源列表)。
    fallback: lexicon -> onnx -> rule（引擎内部完成，总有输出）。
    """
    sources = []

    def repl(m):
        zh, src = word_transliterate(m.group(0))
        sources.append(src)
        return zh

    out = _WORD_RE.sub(repl, text)
    return out, sources
