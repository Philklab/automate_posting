from __future__ import annotations

import re
from typing import Iterable


def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def truncate_to(s: str, max_len: int) -> str:
    s = _collapse_spaces(s)
    if len(s) <= max_len:
        return s
    # Try to cut at word boundary
    cut = s[:max_len].rstrip()
    if " " in cut:
        cut = cut[: cut.rfind(" ")].rstrip()
    return cut


def ensure_length_window(candidates: Iterable[str], min_len: int, max_len: int) -> list[str]:
    out: list[str] = []
    for c in candidates:
        t = _collapse_spaces(c)
        if min_len <= len(t) <= max_len:
            out.append(t)
    return out


def sentence_case(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return s
    return s[0].upper() + s[1:]
