from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import praw


def _get(d: Dict[str, Any], path: str, default=None):
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _build_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=_require_env("REDDIT_CLIENT_ID"),
        client_secret=_require_env("REDDIT_CLIENT_SECRET"),
        username=_require_env("REDDIT_USERNAME"),
        password=_require_env("REDDIT_PASSWORD"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "automate_posting/1.0"),
    )


def run(package: Dict[str, Any], package_dir: Path, dry_run: bool = True) -> Optional[str]:
    cfg = package.get("platforms", {}).get("reddit", {})
    if not cfg.get("enabled"):
        return None

    subreddit = cfg.get("subreddit")
    if not subreddit:
        raise RuntimeError("Reddit enabled but subreddit is missing")

    title = cfg.get("title_override") or package.get("title", "")
    if not title.strip():
        raise RuntimeError("Reddit title is empty")

    post_type = cfg.get("type", "video")  # video | link | text
    flair = cfg.get("flair")

    video_rel = package["media"]["video"]
    video_path = (package_dir / video_rel).resolve()

    body = cfg.get("body") or ""
    link = cfg.get("link")

    # ---- DRY RUN OUTPUT ----
    print("\n[REDDIT]", "DRY-RUN" if dry_run else "REAL-RUN")
    print(f"Subreddit   : r/{subreddit}")
    print(f"Title      : {title}")

    if post_type == "video":
        print(f"Video      : {video_path}")
    elif post_type == "link":
        print(f"Link       : {link or '(missing link)'}")
    else:
        preview = (body[:240] + "…") if len(body) > 240 else body
        print("Body:")
        print(preview)

    if flair:
        print(f"Flair      : {flair}")

    if dry_run:
        return None

    # ---- REAL POSTING ----
    if post_type == "video" and not video_path.exists():
        raise RuntimeError(f"Video file does not exist: {video_path}")

    reddit = _build_reddit_client()
    me = reddit.user.me()
    if not me:
        raise RuntimeError("Reddit authentication failed")

    print(f"Authenticated as: u/{me}")

    if post_type == "video":
        submission = reddit.subreddit(subreddit).submit_video(
            title=title,
            video_path=str(video_path),
            flair_id=None,
        )
    elif post_type == "link":
        submission = reddit.subreddit(subreddit).submit(
            title=title,
            url=link,
            flair_id=None,
        )
    else:
        submission = reddit.subreddit(subreddit).submit(
            title=title,
            selftext=body,
            flair_id=None,
        )

    url = f"https://www.reddit.com{submission.permalink}"
    print(f"✅ Posted: {url}")
    return url
