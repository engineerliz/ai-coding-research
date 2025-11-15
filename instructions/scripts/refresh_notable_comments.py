#!/usr/bin/env python3
"""
Utility script to refresh the Notable Comments tables using cached YouTube
comment exports (e.g., generated via yt-dlp).

Steps:
1. Place `<video_id>.info.json` files under `data/comments/`.
2. Run this script to rebuild every markdown table with the latest rules.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from populate_comments import (
    extract_channel_name_from_markdown,
    extract_video_id_from_content,
    extract_video_id_from_filename,
    get_notable_comments,
    update_markdown_with_comments,
)

CACHE_DIR = Path("data/comments")
PROJECT_ROOT = Path(__file__).parent
CREATORS_DIR = PROJECT_ROOT / "creators"


def load_cached_comments(video_id: str) -> List[Dict]:
    """Convert cached yt-dlp comments into the format populate_comments expects."""
    cache_path = CACHE_DIR / f"{video_id}.info.json"
    if not cache_path.exists():
        print(f"  ⚠️  Comment cache not found for video {video_id}")
        return []
    
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"  ⚠️  Could not parse cache for {video_id}: {exc}")
        return []
    
    raw_comments = data.get("comments", [])
    reply_counts = Counter(
        comment.get("parent")
        for comment in raw_comments
        if comment.get("parent") and comment.get("parent") != "root"
    )
    
    converted: List[Dict] = []
    for raw in raw_comments:
        text = raw.get("text")
        if not text:
            continue
        
        if raw.get("author_is_uploader"):
            # Skip channel-owner comments up front.
            continue
        
        comment_id = raw.get("id")
        is_reply = raw.get("parent") != "root"
        timestamp = raw.get("timestamp")
        published_at = None
        if timestamp:
            try:
                dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
                published_at = dt.isoformat().replace("+00:00", "Z")
            except (TypeError, ValueError, OSError):
                published_at = None
        
        converted.append(
            {
                "text": text,
                "author": raw.get("author", ""),
                "likes": raw.get("like_count", 0),
                "reply_count": 0 if is_reply else reply_counts.get(comment_id, 0),
                "published_at": published_at,
                "timestamp": timestamp,
                "is_reply": is_reply,
                "author_is_uploader": raw.get("author_is_uploader", False),
            }
        )
    
    return converted


def refresh_markdown_file(md_path: Path) -> None:
    """Refresh the notable comments table for a single markdown file."""
    content = md_path.read_text(encoding="utf-8")
    channel_name = extract_channel_name_from_markdown(content)
    video_id = extract_video_id_from_content(content) or extract_video_id_from_filename(md_path.name)
    
    if not video_id:
        print(f"Skipping {md_path}: could not determine video ID")
        return
    
    comments = load_cached_comments(video_id)
    if not comments:
        print(f"Skipping {md_path.name}: no cached comments")
        return
    
    notable = get_notable_comments(
        comments,
        channel_info=None,
        channel_name=channel_name,
        top_n=20,
    )
    
    if not notable:
        print(f"Skipping {md_path.name}: no relevant AI-tool comments")
        return
    
    if update_markdown_with_comments(md_path, notable):
        print(f"✓ Updated {md_path.name}")
    else:
        print(f"✗ Failed to update {md_path.name}")


def main() -> None:
    if not CACHE_DIR.exists():
        print(f"Cache directory not found: {CACHE_DIR}")
        return
    
    markdown_files = sorted(CREATORS_DIR.rglob("*.md"))
    if not markdown_files:
        print("No markdown files found under creators/")
        return
    
    print(f"Processing {len(markdown_files)} markdown files using cached comments...\n")
    for md_file in markdown_files:
        refresh_markdown_file(md_file)


if __name__ == "__main__":
    main()

