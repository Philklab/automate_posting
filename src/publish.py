from pathlib import Path
from typing import Optional, Dict, Any

from adapters import youtube, reddit, instagram
from outbox.reddit_outbox import generate_reddit_outbox


def dispatch(
    package: Dict[str, Any],
    package_dir: Path,
    dry_run: bool = True,
    platform_filter: Optional[str] = None
) -> None:
    """
    Dispatch to enabled adapters.
    package_dir is the folder that contains post_package.json (used to resolve media paths).
    """

    platforms = package.get("platforms", {})
    if not isinstance(platforms, dict):
        raise ValueError("package.platforms must be a dict")

    # Generate Reddit outbox if reddit is enabled (recommended behavior)
    reddit_enabled = bool(platforms.get("reddit", {}).get("enabled", False))
    if reddit_enabled:
        generate_reddit_outbox(package, package_dir)

    def should_run(key: str) -> bool:
        if platform_filter and platform_filter != key:
            return False
        cfg = platforms.get(key, {})
        return isinstance(cfg, dict) and cfg.get("enabled") is True

    if should_run("youtube"):
        youtube.run(package, package_dir=package_dir, dry_run=dry_run)

    if should_run("reddit"):
        reddit.run(package, package_dir=package_dir, dry_run=dry_run)

    if should_run("instagram"):
        instagram.run(package, package_dir=package_dir, dry_run=dry_run)
