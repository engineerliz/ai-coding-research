#!/usr/bin/env python3
"""
Script to populate Notable Comments section in all YouTube video markdown files
under detailed-research directory. Filters for Cursor/competitor-related comments
and excludes channel owner comments.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional

# Import functions from extract_comments.py
from extract_comments import (
    get_video_comments,
    get_youtube_service
)


# Keywords to identify relevant comments about Cursor and competitors
RELEVANT_KEYWORDS = [
    'cursor', 'claude code', 'claudecode', 'codex', 'github copilot', 'copilot',
    'codium', 'tabnine', 'codeium', 'amazon codewhisperer', 'codewhisperer',
    'cursor ai', 'cursor ide', 'cursor editor', 'cursor vs', 'vs cursor',
    'switch to cursor', 'switched to cursor', 'migrate to cursor',
    'switch from cursor', 'switched from cursor', 'migrate from cursor',
    'cursor alternative', 'cursor competitor', 'cursor replacement',
    'better than cursor', 'cursor vs claude', 'claude vs cursor',
    'cursor pricing', 'cursor cost', 'cursor subscription',
    'cursor features', 'cursor update', 'cursor upgrade'
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


def is_channel_owner_comment(comment: Dict, channel_info: Optional[Dict], channel_name: Optional[str]) -> bool:
    """Check if comment is from the channel owner."""
    author = comment.get('author', '').lower()
    
    # Check against channel title
    if channel_info and channel_info.get('channel_title'):
        channel_title = channel_info['channel_title'].lower()
        # Remove common suffixes
        channel_title_clean = re.sub(r'\s*\([^)]+\)\s*$', '', channel_title)
        if author == channel_title_clean.lower() or author == channel_title.lower():
            return True
    
    # Check against channel name from markdown
    if channel_name:
        channel_name_clean = re.sub(r'\s*\([^)]+\)\s*$', '', channel_name).lower()
        if author == channel_name_clean.lower() or author == channel_name.lower():
            return True
    
    # Check for verified channel owner (often has channel ID)
    # Note: We can't easily check this without additional API calls, so we rely on name matching
    
    return False


def calculate_relevance_score(comment_text: str) -> int:
    """Calculate relevance score based on keyword matches."""
    text_lower = comment_text.lower()
    score = 0
    
    # Higher weight for direct mentions
    if 'cursor' in text_lower:
        score += 10
    if 'claude code' in text_lower or 'claudecode' in text_lower:
        score += 8
    if 'codex' in text_lower:
        score += 6
    
    # Medium weight for comparisons
    if 'vs' in text_lower and ('cursor' in text_lower or 'claude' in text_lower):
        score += 5
    if 'switch' in text_lower or 'migrate' in text_lower:
        score += 4
    
    # Lower weight for other mentions
    for keyword in RELEVANT_KEYWORDS:
        if keyword in text_lower:
            score += 1
    
    return score


def get_notable_comments(comments: List[Dict], channel_info: Optional[Dict], 
                        channel_name: Optional[str], top_n: int = 5) -> List[Dict]:
    """
    Select notable comments based on relevance and engagement.
    Filters for Cursor/competitor-related comments and excludes channel owner.
    """
    # Filter out replies for top-level notable comments
    top_level = [c for c in comments if not c.get('is_reply', False)]
    
    # Filter for relevant comments
    relevant = []
    for comment in top_level:
        text = comment.get('text', '')
        
        # Skip if not relevant
        if not is_relevant_comment(text):
            continue
        
        # Skip if from channel owner
        if is_channel_owner_comment(comment, channel_info, channel_name):
            continue
        
        # Calculate scores
        relevance_score = calculate_relevance_score(text)
        engagement_score = comment.get('likes', 0) + (comment.get('reply_count', 0) * 2)
        
        # Combined score: relevance * 10 + engagement (prioritizes relevance but considers engagement)
        comment['relevance_score'] = relevance_score
        comment['engagement_score'] = engagement_score
        comment['combined_score'] = (relevance_score * 10) + engagement_score
        
        relevant.append(comment)
    
    # Sort by combined score (relevance prioritized)
    relevant.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
    
    return relevant[:top_n]


def format_comments_as_table(notable_comments: List[Dict]) -> str:
    """Format comments as a markdown table."""
    if not notable_comments:
        return "| Comment | Author | Engagement |\n|---------|--------|------------|\n| *No relevant comments found* | - | - |\n"
    
    table = "| Comment | Author | Engagement |\n"
    table += "|---------|--------|------------|\n"
    
    for comment in notable_comments:
        text = comment.get('text', '').replace('\n', ' ').strip()
        author = comment.get('author', 'Unknown')
        likes = comment.get('likes', 0)
        reply_count = comment.get('reply_count', 0)
        
        # Truncate very long comments
        if len(text) > 200:
            text = text[:197] + "..."
        
        # Escape pipe characters in text
        text = text.replace('|', '\\|')
        author = author.replace('|', '\\|')
        
        engagement = f"{likes} 👍"
        if reply_count > 0:
            engagement += f", {reply_count} 💬"
        
        table += f"| {text} | {author} | {engagement} |\n"
    
    return table


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
        comments_text = "**Note**: To extract comments, use one of these methods:\n"
        comments_text += "- **YouTube Data API**: Use the provided `extract_comments.py` script with a YouTube API key\n"
        comments_text += "- **Browser Extension**: Use a Chrome extension like \"YouTube Comment Exporter\" \n"
        comments_text += "- **Manual Extraction**: Visit the video and copy notable comments manually\n\n"
        
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

