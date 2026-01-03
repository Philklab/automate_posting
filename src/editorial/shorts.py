from __future__ import annotations

from .utils import truncate_to, ensure_length_window, _collapse_spaces


def derive_youtube_short_titles(meta: dict) -> list[str]:
    """
    Rules (Phase 7):
    - 40–60 chars target
    - one idea
    - present tense vibe
    - no emojis, no hashtags
    """
    epi = meta.get("episode", {}) if isinstance(meta.get("episode"), dict) else {}
    dc = meta.get("dopamine_core", {}) if isinstance(meta.get("dopamine_core"), dict) else {}

    hook = _collapse_spaces(dc.get("hook_line", ""))
    reward = _collapse_spaces(dc.get("reward_moment", ""))
    punch = _collapse_spaces(dc.get("punchline", ""))
    title = _collapse_spaces(epi.get("episode_title", ""))

    raw_candidates = [
        hook,
        reward,
        f"{title} — Live balance test",
        f"{reward} — {punch}",
        f"{hook} — live",
    ]

    # Make a pass: truncate long ones to 60
    candidates = [truncate_to(c, 60) for c in raw_candidates if c]

    # Keep those in window 40–60
    good = ensure_length_window(candidates, 40, 60)

    # If not enough, create tighter variants
    if len(good) < 2:
        variants = []
        if title:
            variants.append(truncate_to(f"{title} — until it breaks", 60))
            variants.append(truncate_to(f"{title} — tension snaps live", 60))
        if hook and len(hook) < 40:
            variants.append(truncate_to(f"{hook} (live)", 60))
        good += ensure_length_window(variants, 40, 60)

    # Deduplicate while preserving order
    seen = set()
    out = []
    for t in good:
        if t not in seen:
            seen.add(t)
            out.append(t)

    return out[:2]
