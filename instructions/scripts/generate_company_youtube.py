#!/usr/bin/env python3
"""
Script to generate YouTube channel research for AI companies.
Requires YOUTUBE_API_KEY environment variable.

Usage:
    python generate_company_youtube.py <channel_id> <company_name> [company_dir]

Examples:
    python generate_company_youtube.py UCchannelID123 Anthropic
    python generate_company_youtube.py UCchannelID123 "Open AI" openai
"""

import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

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
# Check root directory first, then scripts directory
if load_dotenv:
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent  # instructions/scripts -> instructions -> root
    root_env = repo_root / '.env'
    scripts_env = script_dir / '.env'
    
    # Try root directory first, then scripts directory
    if root_env.exists():
        load_dotenv(dotenv_path=root_env)
    elif scripts_env.exists():
        load_dotenv(dotenv_path=scripts_env)


def get_youtube_service(api_key: str):
    """Build and return YouTube Data API service."""
    return build('youtube', 'v3', developerKey=api_key)


def parse_duration(iso_duration: str) -> int:
    """Parse ISO 8601 duration to seconds."""
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, iso_duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def is_short(video: Dict) -> bool:
    """Check if video is a short (≤60 seconds or contains #shorts)."""
    duration_str = video['contentDetails'].get('duration', 'PT0S')
    duration_seconds = parse_duration(duration_str)
    
    title = video['snippet'].get('title', '').lower()
    description = video['snippet'].get('description', '').lower()
    
    return duration_seconds <= 60 or '#shorts' in title or '#short' in title or '#shorts' in description


def is_recent(video: Dict, days: int = 60) -> bool:
    """Check if video was published within last N days."""
    published_str = video['snippet'].get('publishedAt', '')
    try:
        published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
        cutoff = datetime.now(published.tzinfo) - timedelta(days=days)
        return published >= cutoff
    except (ValueError, AttributeError):
        return False


def generate_summary(video: Dict) -> str:
    """Generate a 2-3 sentence summary from video title and description."""
    title = video['snippet'].get('title', '')
    description = video['snippet'].get('description', '')
    
    # Use first paragraph of description, or title if description is short
    desc_text = description.split('\n')[0].strip() if description else ''
    if not desc_text or len(desc_text) < 50:
        desc_text = title
    
    # Create summary (simplified - you may want to use AI/LLM for better summaries)
    # Try to make it 2-3 sentences by splitting on periods
    summary = f"{title}. {desc_text}"
    
    # Truncate if too long, but try to end at a sentence boundary
    if len(summary) > 300:
        truncated = summary[:297]
        last_period = truncated.rfind('.')
        if last_period > 200:  # Only truncate at period if it's not too early
            summary = truncated[:last_period + 1]
        else:
            summary = truncated + "..."
    
    return summary


def get_channel_id_from_url(url_or_id: str) -> Optional[str]:
    """Extract channel ID from URL or return as-is if already an ID."""
    # Channel ID format: UC...
    if url_or_id.startswith('UC') and len(url_or_id) == 24:
        return url_or_id
    
    # Try to extract from various URL formats
    patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'youtube\.com/c/([a-zA-Z0-9_-]+)',
        r'youtube\.com/user/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            # For username/custom URL, we'll need to resolve to channel ID
            # For now, return the match and let the API handle it
            return match.group(1)
    
    return url_or_id


def resolve_channel_id(youtube, identifier: str) -> Optional[str]:
    """Resolve channel ID from username, custom URL, or channel ID."""
    # If it looks like a channel ID, try it directly
    if identifier.startswith('UC') and len(identifier) == 24:
        try:
            response = youtube.channels().list(
                part='id',
                id=identifier
            ).execute()
            if response.get('items'):
                return identifier
        except HttpError:
            pass
    
    # Try as username
    try:
        response = youtube.channels().list(
            part='id',
            forUsername=identifier
        ).execute()
        if response.get('items'):
            return response['items'][0]['id']
    except HttpError:
        pass
    
    # Try as custom URL (handle)
    try:
        # For @username format, remove the @
        handle = identifier.lstrip('@')
        response = youtube.search().list(
            part='snippet',
            q=handle,
            type='channel',
            maxResults=1
        ).execute()
        if response.get('items'):
            return response['items'][0]['id']['channelId']
    except HttpError:
        pass
    
    return None


def get_channel_data(channel_id: str, api_key: str) -> Dict:
    """Get channel overview and all videos."""
    youtube = get_youtube_service(api_key)
    
    # Resolve channel ID if needed
    resolved_id = resolve_channel_id(youtube, channel_id)
    if not resolved_id:
        raise ValueError(f"Could not resolve channel ID from: {channel_id}")
    
    channel_id = resolved_id
    print(f"Using channel ID: {channel_id}")
    
    # Get channel statistics
    print("Fetching channel statistics...")
    channel_response = youtube.channels().list(
        part='statistics,contentDetails,snippet',
        id=channel_id
    ).execute()
    
    if not channel_response.get('items'):
        raise ValueError(f"Channel {channel_id} not found")
    
    channel = channel_response['items'][0]
    stats = channel['statistics']
    channel_title = channel['snippet'].get('title', 'Unknown')
    print(f"Channel: {channel_title}")
    print(f"Subscribers: {stats.get('subscriberCount', '0')}")
    print(f"Total videos: {stats.get('videoCount', '0')}")
    
    # Get all videos
    print("Fetching all videos from channel...")
    all_video_ids = []
    next_page_token = None
    page_count = 0
    
    while True:
        try:
            search_response = youtube.search().list(
                part='id',
                channelId=channel_id,
                type='video',
                maxResults=50,
                order='viewCount',
                pageToken=next_page_token
            ).execute()
            
            page_videos = [item['id']['videoId'] for item in search_response.get('items', [])]
            all_video_ids.extend(page_videos)
            page_count += 1
            print(f"  Fetched page {page_count}: {len(page_videos)} videos (total: {len(all_video_ids)})")
            
            next_page_token = search_response.get('nextPageToken')
            if not next_page_token:
                break
        except HttpError as e:
            print(f"  Error fetching videos: {e}")
            break
    
    if not all_video_ids:
        raise ValueError("No videos found for this channel")
    
    # Get video details in batches
    print(f"Fetching details for {len(all_video_ids)} videos...")
    all_videos = []
    for i in range(0, len(all_video_ids), 50):
        batch_ids = all_video_ids[i:i+50]
        try:
            videos_response = youtube.videos().list(
                part='statistics,contentDetails,snippet',
                id=','.join(batch_ids)
            ).execute()
            all_videos.extend(videos_response.get('items', []))
            print(f"  Processed batch {i//50 + 1}: {len(videos_response.get('items', []))} videos")
        except HttpError as e:
            print(f"  Error fetching video details: {e}")
            continue
    
    # Categorize videos
    print("Categorizing videos...")
    long_form = []
    shorts = []
    recent_count = 0
    
    for video in all_videos:
        if is_short(video):
            shorts.append(video)
        else:
            long_form.append(video)
        
        if is_recent(video):
            recent_count += 1
    
    print(f"  Long-form videos: {len(long_form)}")
    print(f"  Shorts: {len(shorts)}")
    print(f"  Recent posts (last 2 months): {recent_count}")
    
    # Sort by view count
    long_form.sort(key=lambda v: int(v['statistics'].get('viewCount', 0)), reverse=True)
    shorts.sort(key=lambda v: int(v['statistics'].get('viewCount', 0)), reverse=True)
    
    return {
        'channel': channel,
        'stats': stats,
        'long_form': long_form,
        'shorts': shorts,
        'recent_count': recent_count
    }


def format_number(num_str: str) -> str:
    """Format number with commas."""
    try:
        return f"{int(num_str):,}"
    except (ValueError, TypeError):
        return str(num_str)


def generate_posting_frequency_chart(all_videos: List[Dict]) -> str:
    """Generate Mermaid bar chart for posting frequency over the last 12 months."""
    from collections import defaultdict
    
    # Get last 12 months using proper date arithmetic
    now = datetime.now()
    months = []
    for i in range(11, -1, -1):  # Last 12 months, most recent first
        # Calculate month by subtracting months
        target_year = now.year
        target_month = now.month - i
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        month_date = datetime(target_year, target_month, 1)
        months.append(month_date.strftime('%b %Y'))
    
    # Initialize counts for all months
    month_counts = defaultdict(int)
    for month in months:
        month_counts[month] = 0
    
    # Count videos per month
    for video in all_videos:
        published_str = video['snippet'].get('publishedAt', '')
        try:
            published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            month_key = published.strftime('%b %Y')
            
            # Only count if within last 12 months
            if month_key in month_counts:
                month_counts[month_key] += 1
        except (ValueError, AttributeError):
            continue
    
    # Get counts in order
    counts = [month_counts[month] for month in months]
    max_count = max(counts) if counts else 1
    y_max = max_count + 2 if max_count > 0 else 5
    
    # Generate Mermaid chart
    chart = "```mermaid\n"
    chart += "xychart-beta\n"
    chart += '    title "Videos Posted Per Month (Last 12 Months)"\n'
    chart += f'    x-axis [{", ".join(months)}]\n'
    chart += f'    y-axis "Number of Videos" 0 --> {y_max}\n'
    chart += f'    bar [{", ".join(map(str, counts))}]\n'
    chart += "```\n"
    
    return chart


def generate_markdown(company_name: str, channel_data: Dict) -> str:
    """Generate markdown content."""
    stats = channel_data['stats']
    long_form = channel_data['long_form']
    shorts = channel_data['shorts']
    
    md = f"# {company_name} YouTube Channel\n\n"
    md += "## Overview\n\n"
    md += f"- **Subscribers**: {format_number(stats.get('subscriberCount', '0'))}\n"
    md += f"- **Total Videos**: {format_number(stats.get('videoCount', '0'))}\n"
    md += f"- **Long-form Videos**: {len(long_form)}\n"
    md += f"- **Shorts**: {len(shorts)}\n"
    md += f"- **Posts in Last 2 Months**: {channel_data['recent_count']}\n\n"
    md += "---\n\n"
    
    # Posting frequency chart
    md += "## Posting Frequency Over Time\n\n"
    all_videos = long_form + shorts
    md += generate_posting_frequency_chart(all_videos)
    md += "\n---\n\n"
    
    # Long-form videos table
    md += "## Long-form Videos\n\n"
    md += "| Title | Summary | Views |\n"
    md += "|-------|---------|-------|\n"
    
    top_long_form = long_form[:10]
    if not top_long_form:
        md += "| *No long-form videos found* | - | - |\n"
    else:
        for video in top_long_form:
            title = video['snippet'].get('title', 'Untitled').replace('|', '\\|').replace('\n', ' ')
            video_id = video['id']
            url = f"https://www.youtube.com/watch?v={video_id}"
            summary = generate_summary(video).replace('|', '\\|').replace('\n', ' ')
            views = format_number(video['statistics'].get('viewCount', '0'))
            md += f"| [{title}]({url}) | {summary} | {views} |\n"
    
    md += "\n*Top 10 videos by view count*\n\n"
    md += "---\n\n"
    
    # Shorts table
    md += "## Shorts\n\n"
    md += "| Title | Summary | Views |\n"
    md += "|-------|---------|-------|\n"
    
    top_shorts = shorts[:20]
    if not top_shorts:
        md += "| *No shorts found* | - | - |\n"
    else:
        for video in top_shorts:
            title = video['snippet'].get('title', 'Untitled').replace('|', '\\|').replace('\n', ' ')
            video_id = video['id']
            url = f"https://www.youtube.com/watch?v={video_id}"
            summary = generate_summary(video).replace('|', '\\|').replace('\n', ' ')
            views = format_number(video['statistics'].get('viewCount', '0'))
            md += f"| [{title}]({url}) | {summary} | {views} |\n"
    
    md += "\n*Top 20 shorts by view count*\n\n"
    md += "---\n\n"
    md += f"**Last Updated**: {datetime.now().strftime('%m/%d/%Y')}\n"
    
    return md


def normalize_company_dir(company_name: str, company_dir: Optional[str] = None) -> str:
    """Convert company name to directory-friendly format."""
    if company_dir:
        return company_dir.lower().replace(' ', '-')
    
    # Convert to kebab-case
    dir_name = company_name.lower()
    dir_name = re.sub(r'[^a-z0-9\s-]', '', dir_name)
    dir_name = re.sub(r'\s+', '-', dir_name)
    return dir_name


def main():
    """Main entry point."""
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
    
    # Parse arguments
    if len(sys.argv) < 3:
        print("Usage: python generate_company_youtube.py <channel_id_or_url> <company_name> [company_dir]")
        print("\nExamples:")
        print('  python generate_company_youtube.py UCchannelID123 Anthropic')
        print('  python generate_company_youtube.py "https://youtube.com/@anthropic" "Open AI" openai')
        print('\nArguments:')
        print('  channel_id_or_url: YouTube channel ID (UC...) or channel URL')
        print('  company_name: Display name for the company (e.g., "Anthropic")')
        print('  company_dir: Optional directory name (defaults to kebab-case of company_name)')
        sys.exit(1)
    
    channel_identifier = sys.argv[1]
    company_name = sys.argv[2]
    company_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Normalize company directory name
    dir_name = normalize_company_dir(company_name, company_dir)
    
    # Get script directory and resolve repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    output_dir = repo_root / 'ai-companies' / dir_name
    output_path = output_dir / 'youtube.md'
    
    print(f"Company: {company_name}")
    print(f"Output directory: {output_dir}")
    print(f"Output file: {output_path}\n")
    
    try:
        # Fetch channel data
        data = get_channel_data(channel_identifier, api_key)
        
        # Generate markdown
        print("\nGenerating markdown...")
        markdown = generate_markdown(company_name, data)
        
        # Save to file
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding='utf-8')
        
        print(f"\n✓ Successfully generated {output_path}")
        print(f"  Long-form videos: {len(data['long_form'])} (top 10 included)")
        print(f"  Shorts: {len(data['shorts'])} (top 20 included)")
        
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except HttpError as e:
        print(f"\nYouTube API Error: {e}")
        if e.resp.status == 403:
            print("This might be a quota issue. Check your API quota in Google Cloud Console.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

