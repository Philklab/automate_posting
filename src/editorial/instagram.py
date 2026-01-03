from __future__ import annotations

from .utils import sentence_case, _collapse_spaces


def derive_instagram_caption(meta: dict, hashtags: list[str], cta: dict) -> str:
    """
    Rules:
    - hook line
    - short narrative
    - neutral CTA (locked)
    - 5–10 hashtags (we trust upstream already capped; we’ll cap again)
    """
    dc = meta.get("dopamine_core", {}) if isinstance(meta.get("dopamine_core"), dict) else {}

    hook = sentence_case(_collapse_spaces(dc.get("hook_line", "")))
    body = sentence_case(_collapse_spaces(dc.get("core_idea", "")))
    reward = sentence_case(_collapse_spaces(dc.get("reward_moment", "")))

    cta_line = (cta or {}).get("instagram", "") or ""
    cta_line = cta_line.strip()

    # Keep hashtags reasonable
    tags = [h for h in (hashtags or []) if isinstance(h, str) and h.strip()]
    tags = tags[:10]
    tag_line = " ".join(tags)

    parts = []
    if hook:
        parts.append(hook)
    if body:
        parts.append("")
        parts.append(body)
    if reward:
        parts.append("")
        parts.append(reward)
    if cta_line:
        parts.append("")
        parts.append(cta_line)
    if tag_line:
        parts.append("")
        parts.append(tag_line)

    return "\n".join(parts).strip() + "\n"
