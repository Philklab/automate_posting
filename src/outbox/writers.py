from __future__ import annotations

from pathlib import Path


def write_outboxes(run_dir: str, editorial: dict) -> list[str]:
    """
    Writes editorial outbox files under:
      data/out/<run_id>/outbox/
    Returns list of written file paths.
    """
    outbox_dir = Path(run_dir) / "outbox"
    outbox_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []

    # Reddit
    reddit_md = (((editorial or {}).get("reddit") or {}).get("md")) or ""
    if reddit_md.strip():
        p = outbox_dir / "reddit.md"
        p.write_text(reddit_md, encoding="utf-8")
        written.append(str(p))

    # Instagram
    ig_caption = (((editorial or {}).get("instagram") or {}).get("caption")) or ""
    if ig_caption.strip():
        p = outbox_dir / "instagram.txt"
        p.write_text(ig_caption, encoding="utf-8")
        written.append(str(p))

    # TikTok
    tiktok_caption = (((editorial or {}).get("tiktok") or {}).get("caption")) or ""
    pinned = (((editorial or {}).get("tiktok") or {}).get("pinned_comment")) or ""
    if (tiktok_caption.strip() or pinned.strip()):
        p = outbox_dir / "tiktok.txt"
        content = []
        if tiktok_caption.strip():
            content.append(tiktok_caption.strip())
        if pinned.strip():
            content.append("")
            content.append(f"Pinned comment: {pinned.strip()}")
        p.write_text("\n".join(content).strip() + "\n", encoding="utf-8")
        written.append(str(p))

    # Shorts (optional debug artifact)
    shorts = (((editorial or {}).get("shorts") or {}).get("youtube")) or []
    if shorts:
        p = outbox_dir / "youtube_shorts_titles.txt"
        p.write_text("\n".join(shorts).strip() + "\n", encoding="utf-8")
        written.append(str(p))

    return written
