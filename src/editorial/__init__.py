from .cta import CTA_LIBRARY, resolve_cta
from .shorts import derive_youtube_short_titles
from .instagram import derive_instagram_caption
from .reddit import derive_reddit_outbox_md
from .tiktok import derive_tiktok_caption


def derive_editorial(meta: dict, hashtags: list[str]) -> dict:
    """
    Returns a dict with derived editorial content (short titles, captions, reddit outbox).
    This is pure logic: no file IO.
    """
    cta = resolve_cta(meta)

    return {
        "cta": cta,
        "shorts": {
            "youtube": derive_youtube_short_titles(meta),
        },
        "instagram": {
            "caption": derive_instagram_caption(meta, hashtags, cta),
        },
        "reddit": {
            "md": derive_reddit_outbox_md(meta, cta),
        },
        "tiktok": {
            "caption": derive_tiktok_caption(meta),
            "pinned_comment": cta.get("tiktok_pinned_comment", "Full performance on YouTube."),
        },
    }
