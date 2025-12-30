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
    cfg = package.get("platforms", {}).get("instagram", {})
    if not cfg.get("enabled", False):
        return

    ig_type = _get(cfg, "type") or "reel"  # reel | post
    caption = _get(cfg, "caption") or _get(package, "caption") or ""
    hashtags = _get(cfg, "hashtags", []) or []

    video_rel = _get(package, "media.video") or "media/video.mp4"
    base_dir = Path(_get(package, "package_dir", "."))
    video_path = (base_dir / video_rel).resolve()

    print("\n[INSTAGRAM] " + ("DRY-RUN" if dry_run else "REAL-RUN"))
    print(f"Type      : {ig_type}")
    print(f"Media     : {video_path}")

    if caption:
        cap_preview = (caption[:240] + "…") if len(caption) > 240 else caption
        print("Caption:")
        print(cap_preview)

    if hashtags:
        print(f"Hashtags  : {' '.join('#' + h.lstrip('#') for h in hashtags)}")
