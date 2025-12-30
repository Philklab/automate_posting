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


def run(package: Dict[str, Any], package_dir: Path, dry_run: bool = True) -> None:
    cfg = package.get("platforms", {}).get("reddit", {})
    if not cfg.get("enabled"):
        return

    subreddit = cfg.get("subreddit")
    title = cfg.get("title_override") or package.get("title", "")

    post_type = _get(cfg, "type") or "video"  # video | link | text
    flair = _get(cfg, "flair")

    video_rel = package["media"]["video"]
    base_dir = Path(_get(package, "package_dir", "."))
    video_path = (package_dir / video_rel).resolve()

    body = _get(cfg, "body") or ""
    link = _get(cfg, "link")

    print("\n[REDDIT] DRY-RUN")
    print(f"Subreddit   : r/{subreddit}")
    print(f"Title      : {title}")
    print(f"Video      : {video_path}")
    print("Body/Notes : (dry-run only)")

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
