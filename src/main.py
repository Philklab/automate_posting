import json
import os
import shutil
import argparse
import yaml
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from validate import raise_if_invalid, ValidationError
from publish import dispatch

# Phase 9 (editorial expansion)
# NOTE: these imports assume editorial/ and outbox/ are folders inside src/
# and you're running: python src/main.py
from editorial import derive_editorial
from outbox import write_outboxes

load_dotenv()


# -----------------------------
# Helpers
# -----------------------------

def parse_args():
    p = argparse.ArgumentParser(description="automate_posting (Phase 4 orchestrator)")

    p.add_argument("--list-runs", action="store_true", help="List existing run folders in data/out and exit.")
    p.add_argument("--run-id", type=str, default=None, help="Replay an existing run folder in data/out/<run-id>.")
    p.add_argument(
        "--platform",
        type=str,
        default=None,
        choices=["youtube", "reddit", "instagram"],
        help="Run only one platform adapter.",
    )

    # Safe default: dry-run always (unless --confirm is used).
    p.add_argument("--dry-run", action="store_true", help="Force dry-run (default behavior).")
    p.add_argument("--confirm", action="store_true", help="Allow real posting (where supported).")

    return p.parse_args()


def load_metadata_yaml(meta_path: Path) -> dict:
    if not meta_path.exists():
        return {}
    try:
        return yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        raise RuntimeError(f"Invalid metadata.yaml: {meta_path} ({e})")


def _get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _slug_hash(s: str) -> str:
    s = (s or "").strip().lower()
    return "#" + "".join(ch for ch in s if ch.isalnum())


ALLOWED_EPISODE_TYPES = {
    "sound_explained_fast",
    "performance_challenge",
    "drop_science",
    "humor_bit",
}


def validate_metadata_semantic(meta: dict, *, require_ready: bool) -> list[str]:
    errors: list[str] = []

    required = [
        ("episode", "episode_id"),
        ("episode", "episode_title"),
        ("episode", "episode_type"),
        ("dopamine_core", "hook_line"),
        ("dopamine_core", "core_idea"),
        ("dopamine_core", "reward_moment"),
        ("dopamine_core", "punchline"),
        ("release", "week_id"),
        ("release", "package_ready"),
    ]

    for k1, k2 in required:
        v = _get(meta, k1, k2)
        if v in (None, "", []):
            errors.append(f"missing field: {k1}.{k2}")

    et = _get(meta, "episode", "episode_type")
    if et and et not in ALLOWED_EPISODE_TYPES:
        errors.append(f"episode.episode_type invalid: {et}")

    if require_ready and _get(meta, "release", "package_ready") is not True:
        errors.append("release.package_ready must be true")

    return errors


def derive_description(meta: dict) -> str:
    # Phase 7-ish: 3 blocks (intention, context/gear, CTA neutral)
    hook = (_get(meta, "dopamine_core", "hook_line", default="") or "").strip()
    idea = (_get(meta, "dopamine_core", "core_idea", default="") or "").strip()
    reward = (_get(meta, "dopamine_core", "reward_moment", default="") or "").strip()
    punch = (_get(meta, "dopamine_core", "punchline", default="") or "").strip()

    block1 = " ".join([x for x in [hook, idea, reward, punch] if x]).strip()

    genres = _get(meta, "music", "genres", default=[]) or []
    mood = _get(meta, "music", "mood", default=[]) or []
    tempo = _get(meta, "music", "tempo_bpm", default=None)
    key = _get(meta, "music", "key", default=None)

    ctx_lines = []
    if genres:
        ctx_lines.append("Genres: " + ", ".join(genres))
    if mood:
        ctx_lines.append("Mood: " + ", ".join(mood))
    if tempo:
        ctx_lines.append(f"Tempo: {tempo} BPM")
    if key:
        ctx_lines.append(f"Key: {key}")

    gear_lines = []
    for section, label in [
        ("synths", "Synths"),
        ("groovebox", "Groovebox"),
        ("looper", "Looper"),
        ("mixer", "Mixer"),
        ("interface", "Interface"),
    ]:
        items = _get(meta, "gear", section, default=[]) or []
        items = [x for x in items if isinstance(x, str) and x.strip()]
        if items:
            gear_lines.append(f"{label}: " + ", ".join(items))

    block2 = "\n".join([*ctx_lines, *gear_lines]).strip()
    block3 = "Full performance on YouTube."

    return "\n\n".join([b for b in [block1, block2, block3] if b]).strip()


def derive_hashtags(meta: dict) -> list[str]:
    genres = _get(meta, "music", "genres", default=[]) or []
    mood = _get(meta, "music", "mood", default=[]) or []

    tags = ["#electronicmusic", "#liveperformance"]
    for g in genres:
        if isinstance(g, str) and g.strip():
            tags.append(_slug_hash(g))
    for m in mood[:2]:
        if isinstance(m, str) and m.strip():
            tags.append(_slug_hash(m))

    seen = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:12]


def derive_platforms(meta: dict) -> dict:
    pb = _get(meta, "platforms", default={}) or {}

    yt_enabled = bool(_get(pb, "youtube", "enabled", default=True))
    yt_visibility = _get(pb, "youtube", "visibility", default="public")

    rd_enabled = bool(_get(pb, "reddit", "enabled", default=False))
    rd_subreddit = _get(pb, "reddit", "subreddit", default="electronicmusic")

    ig_enabled = bool(_get(pb, "instagram", "enabled", default=False))

    return {
        "youtube": {"enabled": yt_enabled, "visibility": yt_visibility},
        "reddit": {"enabled": rd_enabled, "subreddit": rd_subreddit, "title_override": None},
        "instagram": {"enabled": ig_enabled},
    }


def list_runs(out_root: Path):
    if not out_root.exists():
        print("Available runs: (none)")
        return
    runs = sorted([p.name for p in out_root.iterdir() if p.is_dir()], reverse=True)
    print("Available runs:")
    for r in runs:
        print(f" - {r}")


# -----------------------------
# Main
# -----------------------------

def main():
    args = parse_args()

    project_root = Path(__file__).resolve().parents[1]
    input_dir = Path(os.getenv("INPUT_DIR", project_root / "data" / "in"))
    out_root = Path(os.getenv("OUTPUT_DIR", project_root / "data" / "out"))

    # dry-run is default unless --confirm is provided
    dry_run = True
    if args.confirm:
        dry_run = False
    if args.dry_run:
        dry_run = True

    # ---- LIST MODE
    if args.list_runs:
        list_runs(out_root)
        return

    # ---- REPLAY MODE
    if args.run_id:
        run_out = out_root / args.run_id
        package_path = run_out / "post_package.json"
        if not package_path.exists():
            print(f"ERROR: run-id not found or missing post_package.json: {package_path}")
            raise SystemExit(2)

        try:
            raise_if_invalid(package_path)
            print("✅ Validation OK (replay)")
        except ValidationError as e:
            print(str(e))
            raise SystemExit(2)

        pkg = json.loads(package_path.read_text(encoding="utf-8"))
        dispatch(pkg, package_dir=run_out, dry_run=dry_run, platform_filter=args.platform)
        return

    # ---- GENERATION MODE
    print("=== DRY-RUN: GENERATE PACKAGE ===" if dry_run else "=== REAL-RUN: GENERATE PACKAGE ===")
    print(f"Input:  {input_dir.resolve()}")

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_out = out_root / run_id
    run_out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {run_out.resolve()}")

    # Load metadata.yaml
    meta_path = input_dir / "metadata.yaml"
    meta = load_metadata_yaml(meta_path)

    # Semantic validation (require package_ready only for real runs)
    errors = validate_metadata_semantic(meta, require_ready=(dry_run is False))
    if errors:
        print("\nERROR: metadata.yaml is not valid for generation:")
        for e in errors:
            print(" -", e)
        print(f"\nFix: {meta_path.resolve()}")
        raise SystemExit(2)

    # Copy media
    media_in = input_dir / "media"
    video_in = media_in / "video.mp4"
    thumb_in = media_in / "thumbnail.jpg"

    if not video_in.exists():
        print("ERROR: Missing input video.mp4. Expected:")
        print(f" - {video_in.resolve()}")
        print("Put a test mp4 named video.mp4 in data/in/media/")
        raise SystemExit(2)

    media_out = run_out / "media"
    media_out.mkdir(parents=True, exist_ok=True)

    shutil.copy2(video_in, media_out / "video.mp4")

    thumbnail_out_rel = None
    if thumb_in.exists():
        shutil.copy2(thumb_in, media_out / "thumbnail.jpg")
        thumbnail_out_rel = "media/thumbnail.jpg"

    # Build the post package (v1 spec)
    episode_id = _get(meta, "episode", "episode_id", default=f"package_{run_id}")
    episode_title = _get(meta, "episode", "episode_title", default="Untitled")

    description = derive_description(meta)
    hashtags = derive_hashtags(meta)
    platforms = derive_platforms(meta)

    package = {
        "id": episode_id,
        "title": episode_title,
        "description": description,
        "hashtags": hashtags,
        "media": {"video": "media/video.mp4", "thumbnail": thumbnail_out_rel},
        "platforms": platforms,
        "schedule": {"publish_at": None},
    }

    if not isinstance(package["description"], str) or not package["description"].strip():
        print("\nERROR: metadata.yaml produced an empty description. Fill dopamine_core.* in metadata.yaml.")
        print(f"Fix: {meta_path.resolve()}")
        raise SystemExit(2)

    # Write package
    package_path = run_out / "post_package.json"
    package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")

    # Validate (schema)
    try:
        raise_if_invalid(package_path)
        print("✅ Validation OK")
    except ValidationError as e:
        print(str(e))
        raise SystemExit(2)

    # -------- Phase 9: editorial + outbox generation (NOW INSIDE main)
    editorial = derive_editorial(meta, package.get("hashtags", []))
    written = write_outboxes(str(run_out), editorial)

    if written:
        print("\nOutbox generated:")
        for p in written:
            print(f" - {p}")

    # Dispatch
    pkg = json.loads(package_path.read_text(encoding="utf-8"))
    dispatch(pkg, package_dir=run_out, dry_run=dry_run, platform_filter=args.platform)


if __name__ == "__main__":
    main()
