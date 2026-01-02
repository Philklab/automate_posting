# src/outbox/reddit_outbox.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import textwrap
import datetime


@dataclass(frozen=True)
class SubredditRule:
    name: str
    mode: str  # post | weekly_thread_comment | community_post
    title_hint: str
    notes: str


DEFAULT_SUBREDDIT_RULES: List[SubredditRule] = [
    SubredditRule(
        name="synthesizers",
        mode="weekly_thread_comment",
        title_hint="Live synth performance: Hydrasynth + Digitakt (trance-ish groove)",
        notes="Prefer weekly self-promo thread if available. Keep it discussion/tech-first."
    ),
    SubredditRule(
        name="hydrasynth",
        mode="post",
        title_hint="Hydrasynth live performance — macro/mod-matrix movement in a trance groove",
        notes="Focus on Hydrasynth patch/performance details (macros, mod matrix, aftertouch, arp sync)."
    ),
    SubredditRule(
        name="Elektron",
        mode="post",
        title_hint="Digitakt driving a trance groove — pattern performance + fills (live)",
        notes="Focus on Digitakt workflow (clock, patterns, fills, conditional trigs, resampling if used)."
    ),
    SubredditRule(
        name="loopartists",
        mode="post",
        title_hint="Live looping trance layers — RC-505 performance workflow",
        notes="Focus on looping craft: overdub order, transitions, performance constraints."
    ),
    SubredditRule(
        name="dawless",
        mode="post",
        title_hint="Dawless trance jam — Hydrasynth + Digitakt + RC-505 (no backing track)",
        notes="Emphasize no-DAW + no backing track + sync/routing."
    ),
    SubredditRule(
        name="philklab",
        mode="post",
        title_hint="Episode — live melodic trance earworm (performance)",
        notes="Your own subreddit: ok to be slightly more personal, still keep it Reddit-style."
    ),
]


def _safe_get(d: Dict[str, Any], *keys: str, default=None):
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _infer_gear_lines(description: str) -> List[str]:
    """
    Heuristic: tries to extract 'Gear used:' blocks or bullet-like lines.
    If nothing is found, returns an empty list.
    """
    lines = [ln.strip() for ln in (description or "").splitlines()]
    gear: List[str] = []
    gear_markers = ("gear", "used", "setup")
    in_gear = False

    for ln in lines:
        low = ln.lower()
        if any(m in low for m in gear_markers) and low.endswith(":"):
            in_gear = True
            continue
        if in_gear:
            if not ln:
                break
            # accept bullets or short lines
            if ln.startswith(("-", "*", "•")):
                gear.append(ln.lstrip("-*• ").strip())
            else:
                # stop if it becomes long prose
                if len(ln) > 80:
                    break
                gear.append(ln.strip())

    # fallback: detect known gear names in description
    known = ["Hydrasynth", "Digitakt", "RC-505", "MatrixBrute", "Scarlett", "Yamaha MG"]
    if not gear:
        found = [k for k in known if k.lower() in (description or "").lower()]
        # make them look like bullets
        gear = found

    # de-dup while preserving order
    out: List[str] = []
    seen = set()
    for g in gear:
        if not g:
            continue
        if g.lower() in seen:
            continue
        seen.add(g.lower())
        out.append(g)
    return out


def _build_post_body(package: Dict[str, Any]) -> str:
    """
    Creates a Reddit-friendly body:
    - no emojis
    - no aggressive CTA
    - tech-first
    """
    title = _safe_get(package, "title", default="(untitled)")
    desc = _safe_get(package, "description", default="").strip()
    hashtags = _safe_get(package, "hashtags", default=[]) or []

    gear = _infer_gear_lines(desc)

    # Core body: short + human + technical
    body_lines: List[str] = []
    body_lines.append("Original live performance (no repost, no ads).")
    if desc:
        # keep a short excerpt (avoid dumping full YT description)
        excerpt = desc.splitlines()
        excerpt = [ln.strip() for ln in excerpt if ln.strip()]
        excerpt = excerpt[:3]  # 3 lines max
        if excerpt:
            body_lines.append("")
            body_lines.extend(excerpt)

    if gear:
        body_lines.append("")
        body_lines.append("Gear used:")
        for g in gear[:8]:
            body_lines.append(f"- {g}")

    # Optional: tags as plain words (not #hashtags)
    if hashtags:
        tags = [h.lstrip("#") for h in hashtags if isinstance(h, str)]
        tags = [t for t in tags if t]
        if tags:
            body_lines.append("")
            body_lines.append("Tags:")
            body_lines.append(", ".join(tags[:10]))

    # Soft info line (optional)
    body_lines.append("")
    body_lines.append("Happy to answer questions about the patch / workflow.")

    return "\n".join(body_lines)


def generate_reddit_outbox(
    package: Dict[str, Any],
    package_dir: str | Path,
    subreddit_rules: Optional[List[SubredditRule]] = None,
    max_suggestions: int = 6,
) -> Path:
    """
    Writes outbox/reddit.md under the package_dir folder.
    Returns the path to the created file.
    """
    pkg_dir = Path(package_dir)
    outbox_dir = pkg_dir / "outbox"
    outbox_dir.mkdir(parents=True, exist_ok=True)

    title = _safe_get(package, "title", default="(untitled)")
    media_video_rel = _safe_get(package, "media", "video", default=None)
    video_path = (pkg_dir / media_video_rel).resolve() if media_video_rel else None

    rules = subreddit_rules or DEFAULT_SUBREDDIT_RULES
    rules = rules[:max_suggestions]

    body = _build_post_body(package)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append("# Reddit Posting Outbox")
    md.append("")
    md.append(f"_Generated: {now}_")
    md.append("")
    md.append("## Primary intent")
    md.append("Original live electronic music performance")
    md.append("No repost · No AI · No ads")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Suggested subreddits (choose 1–2 max)")
    md.append("")

    for r in rules:
        md.append(f"### r/{r.name}")
        md.append(f"**Mode:** {r.mode}")
        md.append(f"**Title suggestion:** {r.title_hint}")
        md.append(f"**Notes:** {r.notes}")
        md.append("")

    md.append("---")
    md.append("")
    md.append("## Post body (copy/paste)")
    md.append("")
    md.append(body)
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Media")
    if video_path:
        md.append(f"Video file: `{media_video_rel}`")
        md.append(f"Absolute path (for your reference): `{str(video_path)}`")
    else:
        md.append("Video file: (missing in package)")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Reminder")
    md.append("- Do NOT crosspost")
    md.append("- Post manually")
    md.append("- Engage in comments if people reply")
    md.append("")

    out_path = outbox_dir / "reddit.md"
    out_path.write_text("\n".join(md), encoding="utf-8")
    return out_path
