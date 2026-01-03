from __future__ import annotations


# Locked CTA phrases, deterministic and neutral (Phase 7 rules).
CTA_LIBRARY = {
    "youtube_full": {
        "youtube": "Full performance on YouTube.",
        "instagram": "Full performance on YouTube.",
        "tiktok_pinned_comment": "Full performance on YouTube.",
        "reddit": None,  # Reddit: no CTA line (avoid promo tone)
    },
    "optional_comment": {
        "youtube": "Full performance on YouTube.",
        "instagram": "Full performance on YouTube.",
        "tiktok_pinned_comment": "Full performance on YouTube.",
        "reddit": None,
        "comment_prompt": "Curious what you’d tweak next?",
    },
    "none": {
        "youtube": "",
        "instagram": "",
        "tiktok_pinned_comment": "",
        "reddit": None,
    },
}


def resolve_cta(meta: dict) -> dict:
    """
    Resolve CTA intent from metadata, but keep primary locked to youtube_full.
    If metadata is missing, default safely.
    """
    cta_intent = meta.get("cta_intent", {}) if isinstance(meta.get("cta_intent"), dict) else {}
    primary = cta_intent.get("primary", "youtube_full")

    # Hard-lock requirement: primary must behave as youtube_full even if user typed something else.
    if primary != "youtube_full":
        primary = "youtube_full"

    secondary = cta_intent.get("secondary", "none")
    if secondary not in ("optional_comment", "none"):
        secondary = "none"

    base = dict(CTA_LIBRARY.get(primary, CTA_LIBRARY["youtube_full"]))

    # Add optional comment prompt if requested
    if secondary == "optional_comment":
        base["comment_prompt"] = CTA_LIBRARY["optional_comment"].get("comment_prompt")

    return base
