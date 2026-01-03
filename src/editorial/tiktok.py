from __future__ import annotations

from .utils import _collapse_spaces, truncate_to


def derive_tiktok_caption(meta: dict) -> str:
    """
    TikTok remains manual via outbox; keep it very short.
    """
    dc = meta.get("dopamine_core", {}) if isinstance(meta.get("dopamine_core"), dict) else {}
    punch = _collapse_spaces(dc.get("punchline", ""))
    reward = _collapse_spaces(dc.get("reward_moment", ""))

    base = punch or reward or "Live performance."
    return truncate_to(base, 80)
