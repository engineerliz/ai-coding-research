#!/usr/bin/env python3
"""
Script to extract YouTube comments using YouTube Data API v3
Note: Requires YouTube Data API key in .env file or YOUTUBE_API_KEY environment variable
"""

import os
import sys
import json
from typing import List, Dict, Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Falling back to environment variables only.")
    load_dotenv = None

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: google-api-python-client not installed.")
    print("Install with: pip install google-api-python-client")
    sys.exit(1)

# Load environment variables from .env file
if load_dotenv:
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)


def get_youtube_service(api_key: str):
    """Build and return YouTube Data API service."""
    return build('youtube', 'v3', developerKey=api_key)


def get_video_comments(video_id: str, api_key: str, max_results: int = 100) -> List[Dict]:
    """
    Extract comments from a YouTube video.
    
    Args:
        video_id: YouTube video ID
        api_key: YouTube Data API key
        max_results: Maximum number of comments to retrieve
    
    Returns:
        List of comment dictionaries with text, author, likes, etc.
    """
    try:
        youtube = get_youtube_service(api_key)
        comments = []
        
        # Get top-level comments
        request = youtube.commentThreads().list(
            part='snippet,replies',
            videoId=video_id,
            maxResults=min(max_results, 100),  # API limit is 100 per request
            order='relevance',  # Get most relevant/top comments first
            textFormat='plainText'
        )
        
        while request and len(comments) < max_results:
            response = request.execute()
            
            for item in response.get('items', []):
                top_level_comment = item['snippet']['topLevelComment']['snippet']
                comment_data = {
                    'text': top_level_comment.get('textDisplay', ''),
                    'author': top_level_comment.get('authorDisplayName', ''),
                    'likes': top_level_comment.get('likeCount', 0),
                    'published_at': top_level_comment.get('publishedAt', ''),
                    'updated_at': top_level_comment.get('updatedAt', ''),
                    'is_verified': top_level_comment.get('authorChannelId', {}).get('value') is not None,
                    'reply_count': item['snippet'].get('totalReplyCount', 0)
                }
                comments.append(comment_data)
                
                # Get replies if any
                if 'replies' in item:
                    for reply in item['replies']['comments']:
                        reply_snippet = reply['snippet']
                        reply_data = {
                            'text': reply_snippet.get('textDisplay', ''),
                            'author': reply_snippet.get('authorDisplayName', ''),
                            'likes': reply_snippet.get('likeCount', 0),
                            'published_at': reply_snippet.get('publishedAt', ''),
                            'is_reply': True,
                            'parent_id': item['id']
                        }
                        comments.append(reply_data)
            
            # Get next page if available
            request = youtube.commentThreads().list_next(request, response)
        
        return comments[:max_results]
    
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def get_notable_comments(comments: List[Dict], top_n: int = 5) -> List[Dict]:
    """
    Select notable comments based on engagement (likes, replies).
    
    Args:
        comments: List of comment dictionaries
        top_n: Number of notable comments to return
    
    Returns:
        List of top N notable comments
    """
    # Filter out replies for top-level notable comments
    top_level = [c for c in comments if not c.get('is_reply', False)]
    
    # Sort by engagement score (likes + reply_count * 2)
    top_level.sort(
        key=lambda x: x.get('likes', 0) + (x.get('reply_count', 0) * 2),
        reverse=True
    )
    
    return top_level[:top_n]


def format_comment_for_markdown(comment: Dict, index: int) -> str:
    """Format a comment for markdown insertion."""
    author = comment.get('author', 'Unknown')
    text = comment.get('text', '').replace('\n', ' ').strip()
    likes = comment.get('likes', 0)
    reply_count = comment.get('reply_count', 0)
    
    # Truncate very long comments
    if len(text) > 300:
        text = text[:297] + "..."
    
    engagement = f"{likes} likes"
    if reply_count > 0:
        engagement += f", {reply_count} replies"
    
    return f"{index}. \"{text}\" - {author} ({engagement})"


if __name__ == "__main__":
    # Check for API key (from .env file or environment variable)
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        print("Error: YOUTUBE_API_KEY not set or still has placeholder value.")
        print("\nTo use this script:")
        print("1. Get a YouTube Data API key from: https://console.cloud.google.com/")
        print("2. Add it to the .env file: YOUTUBE_API_KEY=your-actual-key-here")
        print("   OR set it as an environment variable: export YOUTUBE_API_KEY='your-key-here'")
        print("3. Run this script again")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python extract_comments.py <video_id> [max_comments]")
        print("Example: python extract_comments.py WKy71aZHx20 50")
        sys.exit(1)
    
    video_id = sys.argv[1]
    max_comments = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    print(f"Extracting comments from video: {video_id}")
    comments = get_video_comments(video_id, api_key, max_comments)
    
    if not comments:
        print("No comments found or error occurred.")
        sys.exit(1)
    
    print(f"\nFound {len(comments)} comments")
    notable = get_notable_comments(comments, 5)
    
    print("\n=== Notable Comments ===")
    for i, comment in enumerate(notable, 1):
        print(format_comment_for_markdown(comment, i))
    
    # Optionally save to JSON
    if len(sys.argv) > 3 and sys.argv[3] == '--json':
        output_file = f"{video_id}_comments.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)
        print(f"\nAll comments saved to {output_file}")

