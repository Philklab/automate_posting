# src/adapters/youtube.py
from __future__ import annotations

import os
from pathlib import Path
from googleapiclient.http import MediaFileUpload

from youtube_auth import get_youtube_service


def run(package: dict, package_dir: str, dry_run: bool = True) -> None:
    cfg = package.get("platforms", {}).get("youtube", {})
    if not cfg.get("enabled", False):
        return

    title = package.get("title", "").strip()
    description = package.get("description", "").strip()
    visibility = cfg.get("visibility", "unlisted")  # <-- recommandation: unlisted par défaut au début

    video_rel = package["media"]["video"]
    thumb_rel = package["media"].get("thumbnail")

    video_path = str(Path(package_dir) / video_rel)
    thumb_path = str(Path(package_dir) / thumb_rel) if thumb_rel else None

    print("\n[YOUTUBE] " + ("DRY-RUN" if dry_run else "REAL-RUN"))
    print(f"Title      : {title}")
    print(f"Visibility : {visibility}")
    print(f"Video      : {video_path}")
    if thumb_path:
        print(f"Thumbnail  : {thumb_path}")

    if dry_run:
        return

    # --- Real upload ---
    client_secrets = os.environ["YOUTUBE_CLIENT_SECRETS"]
    token_file = os.environ["YOUTUBE_TOKEN_FILE"]

    youtube = get_youtube_service(client_secrets, token_file)

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            # "tags": package.get("hashtags", []),  # optionnel
            # "categoryId": "10",  # Music (optionnel)
        },
        "status": {
            "privacyStatus": visibility
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    insert_request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"Upload progress: {pct}%")

    video_id = response["id"]
    print(f"Uploaded video id: {video_id}")

    # Optional: set thumbnail
    if thumb_path and Path(thumb_path).exists():
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb_path),
        ).execute()
        print("Thumbnail set.")
