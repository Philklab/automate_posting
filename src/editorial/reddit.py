from __future__ import annotations

from .utils import _collapse_spaces, sentence_case


def _format_gear(meta: dict) -> str:
    gear = meta.get("gear", {}) if isinstance(meta.get("gear"), dict) else {}

    # Flatten known lists in a stable order
    order = ["synths", "groovebox", "looper", "mixer", "interface"]
    items: list[str] = []

    for k in order:
        v = gear.get(k)
        if isinstance(v, list):
            items.extend([str(x).strip() for x in v if str(x).strip()])

    # Deduplicate preserving order
    seen = set()
    out = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)

    return " · ".join(out)


def derive_reddit_outbox_md(meta: dict, cta: dict) -> str:
    """
    Reddit is human/manual (no CTA line).
    Tone: factual, human, no emojis, no 'subscribe', no aggressive CTA.
    """
    epi = meta.get("episode", {}) if isinstance(meta.get("episode"), dict) else {}
    dc = meta.get("dopamine_core", {}) if isinstance(meta.get("dopamine_core"), dict) else {}

    episode_id = epi.get("episode_id", "DS-???")
    episode_title = epi.get("episode_title", "Untitled")

    hook = sentence_case(_collapse_spaces(dc.get("hook_line", "")))
    core = sentence_case(_collapse_spaces(dc.get("core_idea", "")))
    reward = sentence_case(_collapse_spaces(dc.get("reward_moment", "")))
    punch = sentence_case(_collapse_spaces(dc.get("punchline", "")))

    gear_line = _format_gear(meta)

    # Optional comment prompt only if intent requested (still neutral)
    comment_prompt = (cta or {}).get("comment_prompt")

    md = []
    md.append(f"## Episode: {episode_id} — {episode_title}")
    md.append("")
    md.append("**Context**")
    if hook:
        md.append(hook)
    if core:
        md.append(core)
    md.append("")
    md.append("**What happens**")
    if reward:
        md.append(reward)
    if punch:
        md.append(punch)
    md.append("")
    if gear_line:
        md.append("**Gear**")
        md.append(gear_line)
        md.append("")

    md.append("**Suggested approach (pick 1–2 subreddits max)**")
    md.append("- r/synthesizers → weekly self-promo thread comment (best practice)")
    md.append("- r/dawless → performance / live constraints angle")
    md.append("- r/hydrasynth → patch/mod-matrix expressivity angle (if relevant)")
    md.append("")
    md.append("_No emojis. No crosspost dump. Keep it technical + human._")

    if comment_prompt:
        md.append("")
        md.append("**Optional closing question**")
        md.append(comment_prompt)

    return "\n".join(md).strip() + "\n"
