# Post Package Specification (v1)

This document defines the standardized structure used by the automation
pipeline to describe a publishable music post.

---

## 1. Purpose

A post package represents **one musical content unit**
that can be published to one or more platforms.

The pipeline must:
1. Generate this package
2. Validate it
3. Pass it to platform adapters

---

## 2. File Structure

Each run generates a folder:

data/out/YYYYMMDD_HHMMSS/

Containing:
- post_package.json
- media/
  - video.mp4
  - thumbnail.jpg (optional)

---

## 3. post_package.json schema

```json
{
  "id": "2025-01-01_dopamine_001",
  "title": "Dirty Bassline Earworm",
  "description": "Live improvised electro-pop jam with heavy bass.",
  "hashtags": ["#electronicmusic", "#synth", "#liveset"],
  "media": {
    "video": "media/video.mp4",
    "thumbnail": "media/thumbnail.jpg"
  },
  "platforms": {
    "youtube": {
      "enabled": true,
      "visibility": "public"
    },
    "reddit": {
      "enabled": true,
      "subreddit": "electronicmusic",
      "title_override": null
    },
    "instagram": {
      "enabled": false
    }
  },
  "schedule": {
    "publish_at": null
  }
}
 