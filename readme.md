# AI Coding Tools YouTube Research Repository

A comprehensive research repository tracking and analyzing YouTube content related to AI coding tools, including official company channels and educational creator content.

## Overview

This repository collects and analyzes YouTube content about AI coding assistants and development tools (primarily Cursor, Claude Code, and related platforms). The research is organized into two main categories:

- **AI Companies**: Analytics and metrics for official YouTube channels of major AI companies
- **AI Creators**: Analysis of educational YouTube videos from content creators, including curated comments and community insights

The repository serves as a centralized resource for understanding how AI coding tools are discussed, marketed, and used in the developer community through YouTube content.

## Repository Structure

### [`ai-companies/`](./ai-companies/)

Research and analytics tracking for AI companies' official YouTube channels. Each company has detailed statistics including:
- Subscriber counts and growth metrics
- Video counts (total, long-form, shorts)
- Posting frequency and activity patterns
- Engagement analytics over time

**Tracked Companies**: Anthropic, Cursor AI, ElevenLabs, Lovable, OpenAI, Perplexity AI, Replit, RunwayML, Vercel

See [`ai-companies/readme.md`](./ai-companies/readme.md) for the complete company analytics table.

### [`creators/`](./creators/)

Analysis of YouTube videos from content creators covering AI coding tools. Each video includes:
- Video metadata (title, views, upload date)
- Video summary
- Curated notable comments
- Comment analysis by themes: **Code Quality**, **Capabilities and Features**, and **Pricing**

The [`creators/readme.md`](./creators/readme.md) synthesizes insights across all videos, organizing community feedback by theme to provide a comprehensive view of developer sentiment.

### [`data/`](./data/)

Raw YouTube video data stored in JSON format, including metadata extracted from YouTube API responses.

### [`instructions/`](./instructions/)

Documentation and scripts for managing and extending the repository:
- **Playbooks**: Step-by-step guides for adding new companies, creators, and videos
- **Scripts**: Python utilities for data extraction, comment analysis, and content generation
- **Analysis Documentation**: Research progress and methodology notes

## How to Use This Repository

### Adding New Content

#### Setting Up Your YouTube API Key

To use the scripts in this repository, you'll need a YouTube Data API v3 key. Follow these steps:

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Select a project" → "New Project"
   - Enter a project name and click "Create"

2. **Enable the YouTube Data API v3**:
   - In the Google Cloud Console, navigate to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click on it and press "Enable"

3. **Create an API Key**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the generated API key

4. **Create your `.env` file**:
   - Create a `.env` file in the root directory of this repository
   - Add the following line (replace `<your api key>` with your actual API key):
   ```
   YOUTUBE_API_KEY=<your api key>
   ```

   **Note**: Make sure to add `.env` to your `.gitignore` file to keep your API key secure and avoid committing it to version control.

1. **Add a New AI Company**: Follow [`instructions/add-company-youtube.md`](./instructions/add-company-youtube.md) to track a new company's YouTube channel.

2. **Add a New Creator Video**: Follow [`instructions/add-new-youtube-video.md`](./instructions/add-new-youtube-video.md) to analyze a new YouTube video from a content creator.

3. **Add Creator Documentation**: Follow [`instructions/add-creator-readme.md`](./instructions/add-creator-readme.md) to add documentation for a new creator.

### Running Scripts

The repository includes Python scripts for automation. See [`instructions/scripts/`](./instructions/scripts/) for:
- `requirements.txt`: Python dependencies
- Data extraction and analysis scripts
- Comment processing utilities

## Research Focus

This repository specifically focuses on:
- **AI Coding Assistants**: Cursor, Claude Code, GitHub Copilot, and similar tools
- **Developer Tooling**: AI-powered development environments and workflows
- **Community Sentiment**: Real user feedback and experiences shared in video comments
- **Content Strategy**: How companies and creators approach YouTube as a communication channel

---

*This repository is maintained for research purposes to track trends, feedback, and discussions about AI coding tools in the YouTube developer community.*