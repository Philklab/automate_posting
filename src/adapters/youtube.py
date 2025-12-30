from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def _get(d: Dict[str, Any], path: str, default=None):
    """Safe getter: path like 'media.video'."""
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def run(package: Dict[str, Any], package_dir: Path, dry_run: bool = True) -> None:
    cfg = package.get("platforms", {}).get("youtube", {})

    if not cfg.get("enabled", False):
        return

    title = _get(cfg, "title") or _get(package, "title") or "(missing title)"
    description = _get(cfg, "description") or _get(package, "description") or ""
    visibility = _get(cfg, "visibility") or "public"

    video_rel = package["media"]["video"]
    thumb_rel = package["media"].get("thumbnail")

    base_dir = Path(_get(package, "package_dir", "."))  # optional; ok if absent
    video_path = (package_dir / video_rel).resolve()
    thumb_path = (package_dir / thumb_rel).resolve() if thumb_rel else None

    tags = _get(cfg, "tags", []) or []

    print("\n[YOUTUBE] " + ("DRY-RUN" if dry_run else "REAL-RUN"))
    print(f"Title      : {title}")
    print(f"Visibility : {visibility}")
    print(f"Video      : {video_path}")
    if thumb_path:
        print(f"Thumbnail  : {thumb_path}")
    if tags:
        print(f"Tags       : {', '.join(map(str, tags))}")

    if description:
        desc_preview = (description[:240] + "…") if len(description) > 240 else description
        print("Description:")
        print(desc_preview)
