# src/validate.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """Raised when the post package is invalid."""


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]


# Matches your actual generated schema
REQUIRED_TOP_LEVEL_KEYS = [
    "id",
    "title",
    "description",
    "media",
    "platforms",
    "schedule",
]

REQUIRED_MEDIA_KEYS = ["video"]


def _as_path(base_dir: Path, maybe_path: Any) -> Optional[Path]:
    """Convert a json value to a Path relative to base_dir when possible."""
    if isinstance(maybe_path, str) and maybe_path.strip():
        p = Path(maybe_path)
        return p if p.is_absolute() else (base_dir / p)
    return None


def load_post_package(package_path: Path) -> Dict[str, Any]:
    if not package_path.exists():
        raise ValidationError(f"post_package.json not found: {package_path}")

    try:
        with package_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {package_path}: {e}") from e

    if not isinstance(data, dict):
        raise ValidationError(f"Top-level JSON must be an object/dict in {package_path}")

    return data


def validate_post_package(package_path: Path) -> ValidationResult:
    errors: List[str] = []
    base_dir = package_path.parent

    # 1) Load JSON
    try:
        data = load_post_package(package_path)
    except ValidationError as e:
        return ValidationResult(ok=False, errors=[str(e)])

    # 2) Required top-level keys
    for k in REQUIRED_TOP_LEVEL_KEYS:
        if k not in data:
            errors.append(f"Missing top-level key: '{k}'")

    # 3) id/title/description validation
    _id = data.get("id")
    if not isinstance(_id, str) or not _id.strip():
        errors.append("id must be a non-empty string")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string")

    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("description must be a non-empty string")

    # 4) hashtags (optional but if present must be list[str])
    hashtags = data.get("hashtags", None)
    if hashtags is not None:
        if not isinstance(hashtags, list) or not all(isinstance(h, str) for h in hashtags):
            errors.append("hashtags must be a list of strings (e.g. ['#tag1', '#tag2'])")

    # 5) media validation
    media = data.get("media")
    if not isinstance(media, dict):
        errors.append("media must be an object/dict")
        media = {}

    for k in REQUIRED_MEDIA_KEYS:
        if k not in media:
            errors.append(f"Missing media key: 'media.{k}'")

    video_path = _as_path(base_dir, media.get("video"))
    if video_path is None:
        errors.append("media.video must be a non-empty string path")
    elif not video_path.exists():
        errors.append(f"media.video file not found: {video_path}")

    thumb_path = _as_path(base_dir, media.get("thumbnail"))
    if thumb_path is not None and not thumb_path.exists():
        errors.append(f"media.thumbnail file not found: {thumb_path}")

    # 6) platforms validation
    platforms = data.get("platforms")
    if not isinstance(platforms, dict):
        errors.append("platforms must be an object/dict")
        platforms = {}

    enabled_platforms: List[str] = []
    for name, cfg in platforms.items():
        if not isinstance(name, str):
            continue
        if not isinstance(cfg, dict):
            errors.append(f"platforms.{name} must be an object/dict")
            continue

        enabled = cfg.get("enabled", False)
        if enabled is True:
            enabled_platforms.append(name)

        # platform-specific checks (light but useful)
        if name.lower() == "reddit" and enabled is True:
            sub = cfg.get("subreddit")
            if not isinstance(sub, str) or not sub.strip():
                errors.append("platforms.reddit.subreddit must be a non-empty string when reddit is enabled")

        if name.lower() == "youtube" and enabled is True:
            vis = cfg.get("visibility", "public")
            if vis not in {"public", "unlisted", "private"}:
                errors.append("platforms.youtube.visibility must be one of: public, unlisted, private")

    if len(enabled_platforms) == 0:
        errors.append("No platform enabled. Set at least one: platforms.<name>.enabled = true")

    # 7) schedule validation
    schedule = data.get("schedule")
    if not isinstance(schedule, dict):
        errors.append("schedule must be an object/dict")
        schedule = {}

    publish_at = schedule.get("publish_at", None)
    if publish_at is not None and not (isinstance(publish_at, str) and publish_at.strip()):
        errors.append("schedule.publish_at must be null or a non-empty string (ISO datetime recommended)")

    return ValidationResult(ok=(len(errors) == 0), errors=errors)


def raise_if_invalid(package_path: Path) -> None:
    res = validate_post_package(package_path)
    if not res.ok:
        msg = "Post package validation failed:\n" + "\n".join(f"- {e}" for e in res.errors)
        raise ValidationError(msg)
