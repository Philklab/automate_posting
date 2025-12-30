from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def _get(d: Dict[str, Any], path: str, default=None):
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def run(package: Dict[str, Any], dry_run: bool = True) -> None:
    cfg = package.get("platforms", {}).get("reddit", {})

    if not cfg.get("enabled", False):
        return

    subreddit = _get(cfg, "subreddit") or "(missing subreddit)"
    title = _get(cfg, "title_override") or _get(package, "title") or "(missing title)"

    post_type = _get(cfg, "type") or "video"  # video | link | text
    flair = _get(cfg, "flair")

    video_rel = _get(package, "media.video") or "media/video.mp4"
    base_dir = Path(_get(package, "package_dir", "."))
    video_path = (base_dir / video_rel).resolve()

    body = _get(cfg, "body") or ""
    link = _get(cfg, "link")

    print("\n[REDDIT] " + ("DRY-RUN" if dry_run else "REAL-RUN"))
    print(f"Subreddit : {subreddit}")
    print(f"Title     : {title}")
    print(f"Post type : {post_type}")

    if post_type == "video":
        print(f"Media     : {video_path}")
    elif post_type == "link":
        print(f"Link      : {link or '(missing link)'}")
    else:
        body_preview = (body[:240] + "…") if len(body) > 240 else body
        print("Body:")
        print(body_preview)

    if flair:
        print(f"Flair     : {flair}")
