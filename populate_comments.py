#!/usr/bin/env python3
"""
Script to populate Notable Comments section in all YouTube video markdown files
under detailed-research directory. Filters for Cursor/competitor-related comments
and excludes channel owner comments.
"""

import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

get_video_comments = None
get_youtube_service = None


def _ensure_extract_comments_loaded() -> None:
    """Lazily import extract_comments functions only when needed."""
    global get_video_comments, get_youtube_service
    if get_video_comments is not None and get_youtube_service is not None:
        return
    
    try:
        from extract_comments import (  # type: ignore import-not-found
            get_video_comments as _get_video_comments,
            get_youtube_service as _get_youtube_service,
        )
    except ImportError as exc:  # pragma: no cover - import-time safeguard
        raise ImportError(
            "extract_comments dependencies are missing. "
            "Install google-api-python-client (and python-dotenv) to use the API-powered workflow."
        ) from exc
    
    get_video_comments = _get_video_comments
    get_youtube_service = _get_youtube_service


# Keywords to identify relevant comments about Cursor and competitors
RELEVANT_KEYWORDS = [
    # Cursor & variants
    'cursor', 'cursor ai', 'cursor ide', 'cursor editor', 'cursor cli',
    'cursor vs', 'vs cursor', 'cursor features', 'cursor pricing',
    'cursor cost', 'cursor subscription', 'cursor update', 'cursor upgrade',
    'switch to cursor', 'switched to cursor', 'migrate to cursor',
    'switch from cursor', 'switched from cursor', 'migrate from cursor',
    'cursor alternative', 'cursor competitor', 'cursor replacement',
    # Claude family
    'claude code', 'claudecode', 'claude desktop', 'claude', 'sonnet', 'opus',
    'claude vs cursor', 'cursor vs claude',
    # Other AI coding tools
    'codex', 'windsurf', 'github copilot', 'copilot', 'tabnine', 'codium',
    'codeium', 'amazon codewhisperer', 'codewhisperer', 'code whisperer',
    'replit', 'replit agent', 'blackbox', 'aider', 'phind', 'supermaven',
    'devin', 'gemini', 'chatgpt', 'gpt-4', 'gpt4', 'gpt-5', 'gpt5',
    'moonbeam', 'bolt.new', 'bolt new', 'kiro', 'deepseek', 'aws q developer',
    'q developer', 'codegeex', 'cursor competitor', 'cursor alternative'
]


def extract_channel_name_from_markdown(content: str) -> Optional[str]:
    """Extract channel name from markdown file content."""
    match = re.search(r'\*\*Channel\*\*:\s*(.+?)(?:\n|$)', content)
    if match:
        channel_name = match.group(1).strip()
        # Remove common suffixes like "(Builder.io)" or other parentheticals
        channel_name = re.sub(r'\s*\([^)]+\)\s*$', '', channel_name)
        return channel_name
    return None


def get_channel_owner_from_video(video_id: str, api_key: str) -> Optional[Dict]:
    """Get channel owner information from video metadata."""
    _ensure_extract_comments_loaded()
    try:
        youtube = get_youtube_service(api_key)
        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()
        
        if response.get('items'):
            snippet = response['items'][0]['snippet']
            return {
                'channel_id': snippet.get('channelId'),
                'channel_title': snippet.get('channelTitle'),
                'channel_custom_url': snippet.get('customUrl')
            }
    except Exception as e:
        print(f"  Warning: Could not get channel info: {e}")
    return None


def is_relevant_comment(comment_text: str) -> bool:
    """Check if comment is relevant (mentions Cursor or competitors)."""
    text_lower = comment_text.lower()
    return any(keyword in text_lower for keyword in RELEVANT_KEYWORDS)


def _normalize_author_name(name: str) -> str:
    """Normalize an author or channel name for comparison."""
    if not name:
        return ''
    normalized = name.strip().lower()
    normalized = normalized.lstrip('@')
    normalized = re.sub(r'\s*\([^)]+\)\s*$', '', normalized)
    normalized = re.sub(r'[^a-z0-9]+', '', normalized)
    return normalized


def is_channel_owner_comment(comment: Dict, channel_info: Optional[Dict], channel_name: Optional[str]) -> bool:
    """Check if comment is from the channel owner."""
    if comment.get('author_is_uploader'):
        return True
    
    author_norm = _normalize_author_name(comment.get('author', ''))
    if not author_norm:
        return False
    
    # Check against channel title
    if channel_info and channel_info.get('channel_title'):
        channel_title_norm = _normalize_author_name(channel_info['channel_title'])
        if author_norm == channel_title_norm:
            return True
    
    # Check against channel name from markdown
    if channel_name:
        channel_name_norm = _normalize_author_name(channel_name)
        if author_norm == channel_name_norm:
            return True
    
    return False


def get_notable_comments(comments: List[Dict], channel_info: Optional[Dict], 
                        channel_name: Optional[str], top_n: int = 20) -> List[Dict]:
    """
    Select notable comments based on relevance and engagement.
    Filters for Cursor/competitor-related comments and excludes channel owner.
    """
    relevant = []
    for comment in comments:
        text = comment.get('text', '')
        
        if not text or not is_relevant_comment(text):
            continue
        
        if is_channel_owner_comment(comment, channel_info, channel_name):
            continue
        
        likes = comment.get('likes', 0)
        reply_count = comment.get('reply_count', 0)
        engagement_score = likes + reply_count
        comment['engagement_score'] = engagement_score
        relevant.append(comment)
    
    relevant.sort(
        key=lambda x: (
            x.get('engagement_score', 0),
            x.get('likes', 0),
            _get_comment_timestamp(x)
        ),
        reverse=True
    )
    
    return relevant[:top_n]


def _get_comment_timestamp(comment: Dict) -> int:
    """Return a comparable timestamp for sorting (UTC seconds)."""
    published_at = comment.get('published_at') or comment.get('updated_at')
    if published_at:
        try:
            dt = datetime.fromisoformat(
                published_at.replace('Z', '+00:00')
            )
            return int(dt.timestamp())
        except ValueError:
            pass
    
    if comment.get('timestamp'):
        try:
            return int(comment['timestamp'])
        except (TypeError, ValueError):
            return 0
    
    return 0


def format_comments_as_table(notable_comments: List[Dict]) -> str:
    """Format comments as a markdown table."""
    if not notable_comments:
        return "| Comment | Date | Engagement |\n|---------|------|------------|\n| *No relevant comments found* | - | - |\n"
    
    table = "| Comment | Date | Engagement |\n"
    table += "|---------|------|------------|\n"
    
    for comment in notable_comments:
        text = comment.get('text', '').replace('\n', '<br>').strip()
        likes = comment.get('likes', 0)
        reply_count = comment.get('reply_count', 0)
        engagement_parts = [f"{likes} 👍"]
        if reply_count > 0:
            engagement_parts.append(f"{reply_count} 💬")
        engagement = ", ".join(part for part in engagement_parts if part)
        
        # Escape pipe characters in text
        text = text.replace('|', '\\|')
        
        table += f"| {text} | {format_comment_date(comment)} | {engagement or '0 👍'} |\n"
        
    return table


def format_comment_date(comment: Dict) -> str:
    """Return yyyy-mm-dd date for the comment."""
    published_at = comment.get('published_at') or comment.get('updated_at')
    if published_at:
        try:
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    if comment.get('timestamp'):
        try:
            dt = datetime.fromtimestamp(int(comment['timestamp']), tz=timezone.utc)
            return dt.strftime('%Y-%m-%d')
        except (TypeError, ValueError, OSError):
            pass
    
    relative = comment.get('_time_text')
    if relative:
        return relative
    
    return '-'


def update_markdown_with_comments(markdown_path: Path, notable_comments: List[Dict]) -> bool:
    """
    Update the Notable Comments section in a markdown file with table format.
    
    Returns True if successful, False otherwise.
    """
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the Notable Comments section
        # Pattern: from "### Notable Comments" to the next "---" or "##"
        # Match everything including numbered lists and blank lines
        pattern = r'(### Notable Comments\n\n)(.*?)(\n\n---|\n##|\Z)'
        
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        if not match:
            print(f"  Warning: Could not find 'Notable Comments' section in {markdown_path.name}")
            return False
        
        # Generate the new comments section
        generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        comments_text = (
            f"**Note**: Comments captured on {generated_at} and filtered for explicit mentions "
            "of Cursor, Claude Code, Codex, Windsurf, or other AI coding tools. "
            "Sorted by engagement (likes + replies) and capped at 20 entries.\n\n"
        )
        
        # Add table
        comments_text += format_comments_as_table(notable_comments) + "\n"
        
        # Replace the entire section - match.group(3) should be the separator (--- or ##)
        # We need to preserve the newlines before the separator
        separator = match.group(3)
        if separator.startswith('\n\n---'):
            separator = '\n\n---'
        elif separator.startswith('\n##'):
            separator = '\n##'
        
        new_content = content[:match.start()] + match.group(1) + comments_text + separator
        
        # Write back to file
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    
    except Exception as e:
        print(f"  Error updating {markdown_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_all_markdown_files(research_dir: Path, api_key: str, max_comments: int = 100):
    """Process all markdown files in the research directory."""
    _ensure_extract_comments_loaded()
    # Find all markdown files
    md_files = list(research_dir.rglob("*.md"))
    
    if not md_files:
        print(f"No markdown files found in {research_dir}")
        return
    
    print(f"Found {len(md_files)} markdown files to process\n")
    
    success_count = 0
    error_count = 0
    
    for md_file in md_files:
        # Extract video ID from filename
        video_id = extract_video_id_from_filename(md_file.name)
        
        # Read markdown to get channel name
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            channel_name = extract_channel_name_from_markdown(content)
            
            # Also try to extract video ID from content as backup
            content_video_id = extract_video_id_from_content(content)
            if content_video_id and content_video_id != video_id:
                print(f"  Warning: Video ID mismatch in {md_file.name} (filename: {video_id}, content: {content_video_id})")
                video_id = content_video_id
        except Exception as e:
            print(f"  Error reading {md_file.name}: {e}")
            continue
        
        print(f"Processing: {md_file.name} (Video ID: {video_id}, Channel: {channel_name or 'Unknown'})")
        
        # Get channel owner info from YouTube API
        channel_info = get_channel_owner_from_video(video_id, api_key)
        if channel_info:
            print(f"  Channel owner: {channel_info.get('channel_title', 'Unknown')}")
        
        # Get comments
        comments = get_video_comments(video_id, api_key, max_comments)
        
        if not comments:
            print(f"  No comments found for video {video_id}")
            notable = []
        else:
            print(f"  Found {len(comments)} total comments")
            notable = get_notable_comments(comments, channel_info, channel_name, 5)
            print(f"  Selected {len(notable)} relevant comments (Cursor/competitor-related, excluding channel owner)")
        
        # Update markdown file
        if update_markdown_with_comments(md_file, notable):
            print(f"  ✓ Updated {md_file.name}\n")
            success_count += 1
        else:
            print(f"  ✗ Failed to update {md_file.name}\n")
            error_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Successfully processed: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total: {len(md_files)}")


def extract_video_id_from_filename(filename: str) -> str:
    """Extract video ID from markdown filename (e.g., WKy71aZHx20.md -> WKy71aZHx20)."""
    return Path(filename).stem


def extract_video_id_from_content(content: str) -> str:
    """Extract video ID from markdown file content."""
    match = re.search(r'\*\*Video ID\*\*:\s*(\S+)', content)
    if match:
        return match.group(1)
    return None


if __name__ == "__main__":
    # Check for API key
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        print("Error: YOUTUBE_API_KEY not set or still has placeholder value.")
        print("\nTo use this script:")
        print("1. Get a YouTube Data API key from: https://console.cloud.google.com/")
        print("2. Add it to the .env file: YOUTUBE_API_KEY=your-actual-key-here")
        print("   OR set it as an environment variable: export YOUTUBE_API_KEY='your-key-here'")
        print("3. Run this script again")
        sys.exit(1)
    
    # Get research directory
    script_dir = Path(__file__).parent
    research_dir = script_dir / "detailed-research"
    
    if not research_dir.exists():
        print(f"Error: Research directory not found: {research_dir}")
        sys.exit(1)
    
    # Optional: max comments per video (default 100)
    max_comments = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    
    print(f"Processing markdown files in: {research_dir}")
    print(f"Max comments per video: {max_comments}")
    print(f"Filtering for: Cursor and competitor-related comments only")
    print(f"Excluding: Channel owner comments\n")
    
    process_all_markdown_files(research_dir, api_key, max_comments)

