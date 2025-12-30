import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from validate import raise_if_invalid, ValidationError

load_dotenv()

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
    input_dir = Path(os.getenv("INPUT_DIR", "./data/in"))
    output_dir = Path(os.getenv("OUTPUT_DIR", "./data/out"))

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_out = output_dir / run_id
    media_out = run_out / "media"
    media_out.mkdir(parents=True, exist_ok=True)

    print("=== DRY RUN: GENERATE PACKAGE ===")
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
            "thumbnail": thumbnail_out_rel
        },
        "platforms": {
            "youtube": {
                "enabled": str_to_bool(meta.get("youtube_enabled", "true"), True),
                "visibility": meta.get("youtube_visibility", "public")
            },
            "reddit": {
                "enabled": str_to_bool(meta.get("reddit_enabled", "false"), False),
                "subreddit": meta.get("reddit_subreddit", "electronicmusic"),
                "title_override": None
            },
            "instagram": {
                "enabled": str_to_bool(meta.get("instagram_enabled", "false"), False)
            }
        },
        "schedule": {
            "publish_at": None
        }
    }

    # If no thumbnail, write null explicitly (JSON None)
    if package["media"]["thumbnail"] is None:
        package["media"]["thumbnail"] = None

    # Write package
    package_path = run_out / "post_package.json"
    package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        raise_if_invalid(Path(out_dir) / "post_package.json")
        print("✅ Validation OK")
    except ValidationError as e:
        print(str(e))
        raise SystemExit(2)


    print("\nGenerated:")
    print(f" - {package_path.resolve()}")
    print(f" - {video_out.resolve()}")
    if thumbnail_out_rel:
        print(f" - {(media_out / 'thumbnail.jpg').resolve()}")

    print("\nNext: validate schema + create platform adapters (still dry-run).")

if __name__ == "__main__":
    main()
