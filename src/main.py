import json
import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from validate import raise_if_invalid, ValidationError
from publish import dispatch

load_dotenv()


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

    # Safe default: dry-run always. This flag just makes it explicit.
    p.add_argument("--dry-run", action="store_true", help="Force dry-run (default behavior).")

    # DANGEROUS: enables real posting when supported by adapters
    p.add_argument(
        "--confirm",
        action="store_true",
        help="Enable REAL posting (dangerous). Without this flag, nothing is ever published.",
    )

    return p.parse_args()


def parse_meta(meta_path: Path) -> dict:
    """
    Very small key=value parser.
    Lines starting with # or empty lines are ignored.
    """
    meta = {}
    if not meta_path.exists():
        return meta

    for line in meta_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        meta[k.strip()] = v.strip()
    return meta


def str_to_bool(s: str, default=False) -> bool:
    if s is None:
        return default
    return s.lower() in ("1", "true", "yes", "y", "on")


def main():
    args = parse_args()

    # ---- EXECUTION MODE (SAFETY FIRST) ----
    # Default: ALWAYS dry-run
    dry_run = True

    # Real posting is allowed ONLY with --confirm (adapters may still choose to stay dry-run if not implemented)
    if args.confirm:
        dry_run = False

    # ---- LIST RUNS MODE ----
    if args.list_runs:
        out_dir = Path("data") / "out"

        if not out_dir.exists():
            print("No data/out folder found.")
            return

        runs = sorted([p.name for p in out_dir.iterdir() if p.is_dir()], reverse=True)

        if not runs:
            print("No runs found in data/out/")
            return

        print("Available runs:")
        for r in runs:
            print(" -", r)
        return

    # ---- REPLAY MODE ----
    if args.run_id:
        package_dir = Path("data") / "out" / args.run_id
        package_path = package_dir / "post_package.json"

        if not package_path.exists():
            print(f"ERROR: post_package.json not found: {package_path.resolve()}")
            return

        try:
            raise_if_invalid(package_path)
            print("✅ Validation OK (replay)")
        except ValidationError as e:
            print(str(e))
            raise SystemExit(2)

        pkg = json.loads(package_path.read_text(encoding="utf-8"))
        dispatch(pkg, package_dir=package_dir, dry_run=dry_run, platform_filter=args.platform)
        return

    # ---- GENERATION MODE ----
    input_dir = Path(os.getenv("INPUT_DIR", "./data/in"))
    output_dir = Path(os.getenv("OUTPUT_DIR", "./data/out"))

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_out = output_dir / run_id
    media_out = run_out / "media"
    media_out.mkdir(parents=True, exist_ok=True)

    mode_label = "DRY-RUN" if dry_run else "REAL-RUN"
    print(f"=== {mode_label}: GENERATE PACKAGE ===")
    print(f"Input:  {input_dir.resolve()}")
    print(f"Output: {run_out.resolve()}")

    # Input expectations
    meta_path = input_dir / "meta.txt"
    media_in = input_dir / "media"
    video_in = media_in / "video.mp4"
    thumb_in = media_in / "thumbnail.jpg"

    meta = parse_meta(meta_path)

    if not video_in.exists():
        print("\nERROR: Missing input video:")
        print(f"Expected: {video_in.resolve()}")
        print("Add a file named video.mp4 in data/in/media/")
        return

    # Copy media into the package output
    video_out = media_out / "video.mp4"
    shutil.copy2(video_in, video_out)

    thumbnail_out_rel = None
    if thumb_in.exists():
        thumb_out = media_out / "thumbnail.jpg"
        shutil.copy2(thumb_in, thumb_out)
        thumbnail_out_rel = "media/thumbnail.jpg"

    # Build the post package (v1 spec)
    package = {
        "id": meta.get("id", f"package_{run_id}"),
        "title": meta.get("title", "Untitled"),
        "description": meta.get("description", ""),
        "hashtags": [h.strip() for h in meta.get("hashtags", "").split(",") if h.strip()],
        "media": {
            "video": "media/video.mp4",
            "thumbnail": thumbnail_out_rel,
        },
        "platforms": {
            "youtube": {
                "enabled": str_to_bool(meta.get("youtube_enabled", "true"), True),
                "visibility": meta.get("youtube_visibility", "public"),
            },
            "reddit": {
                "enabled": str_to_bool(meta.get("reddit_enabled", "false"), False),
                "subreddit": meta.get("reddit_subreddit", "electronicmusic"),
                "title_override": None,
            },
            "instagram": {
                "enabled": str_to_bool(meta.get("instagram_enabled", "false"), False),
            },
        },
        "schedule": {
            "publish_at": None,
        },
    }

    # If no thumbnail, write null explicitly (JSON None)
    if package["media"]["thumbnail"] is None:
        package["media"]["thumbnail"] = None

    # Write package
    package_path = run_out / "post_package.json"
    package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        raise_if_invalid(package_path)
        print("✅ Validation OK")
    except ValidationError as e:
        print(str(e))
        raise SystemExit(2)

    # ---- DISPATCH ----
    pkg = json.loads(package_path.read_text(encoding="utf-8"))
    dispatch(pkg, package_dir=run_out, dry_run=dry_run, platform_filter=args.platform)

    print("\nGenerated:")
    print(f" - {package_path.resolve()}")
    print(f" - {video_out.resolve()}")
    if thumbnail_out_rel:
        print(f" - {(media_out / 'thumbnail.jpg').resolve()}")

    print("\nNext: Phase 5 adapters can use --confirm for real posting (dry-run is always the default).")


if __name__ == "__main__":
    main()
