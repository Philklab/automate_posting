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


REQUIRED_TOP_LEVEL_KEYS = [
    "version",
    "created_utc",
    "media",
    "meta",
    "platforms",
]

REQUIRED_META_KEYS = [
    "title",
    "description",
]

REQUIRED_MEDIA_KEYS = [
    "video",
]

# Platforms you currently plan to support (expand later)
KNOWN_PLATFORMS = {"youtube", "reddit", "instagram", "facebook", "tiktok"}


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
    """
    Validate the generated post_package.json file and referenced assets.

    package_path: path to .../post_package.json
    """
    errors: List[str] = []
    base_dir = package_path.parent

    # 1) Load JSON
    try:
        data = load_post_package(package_path)
    except ValidationError as e:
        return ValidationResult(ok=False, errors=[str(e)])

    # 2) Required keys
    for k in REQUIRED_TOP_LEVEL_KEYS:
        if k not in data:
            errors.append(f"Missing top-level key: '{k}'")

    # 3) meta validation
    meta = data.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta must be an object/dict")
        meta = {}

    for k in REQUIRED_META_KEYS:
        v = meta.get(k)
        if not isinstance(v, str) or not v.strip():
            errors.append(f"meta.{k} must be a non-empty string")

    # 4) media validation
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

    # Optional thumbnail
    thumb_path = _as_path(base_dir, media.get("thumbnail"))
    if thumb_path is not None and not thumb_path.exists():
        errors.append(f"media.thumbnail file not found: {thumb_path}")

    # 5) platforms validation
    platforms = data.get("platforms")
    if not isinstance(platforms, dict):
        errors.append("platforms must be an object/dict")
        platforms = {}

    # Normalize “enabled” detection for any platform object
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

        # Gentle warning if unknown platform key is used (not a hard error)
        # We won't add as error; we keep it future-proof.
        # If you want strict mode later, flip this into an error.
        if name.lower() not in KNOWN_PLATFORMS:
            pass

    if len(enabled_platforms) == 0:
        errors.append("No platform enabled. Set at least one: platforms.<name>.enabled = true")

    # 6) version sanity (non-empty)
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        errors.append("version must be a non-empty string")

    # 7) created_utc sanity (number)
    created = data.get("created_utc")
    if not isinstance(created, (int, float)):
        errors.append("created_utc must be a unix timestamp number (int/float)")

    return ValidationResult(ok=(len(errors) == 0), errors=errors)


def raise_if_invalid(package_path: Path) -> None:
    res = validate_post_package(package_path)
    if not res.ok:
        msg = "Post package validation failed:\n" + "\n".join(f"- {e}" for e in res.errors)
        raise ValidationError(msg)
