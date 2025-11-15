# Add a New YouTube Video Analysis

This playbook walks you through adding a fresh video analysis entry to the repo whether you are doing it manually or orchestrating it via Cursor. Follow the steps in order; each one mirrors the current repo conventions.

---

## 1. Collect Input

1. Get the YouTube URL from the requester.
2. Derive the video ID (the `v` parameter).
3. Identify the creator’s display name exactly as it should appear under `creators/{creator-name}` (kebab case, capitalize first letters, spaces become `-`).
4. Capture the exact video title (sanitize only when creating file paths).

---

## 2. Create Directory Structure

1. Confirm the creator directory exists at `/Users/liz/dev/cursor-research/creators/{Creator-Name}/youtube`.  
   - If missing, create it (including intermediate folders).
2. Inside `youtube/`, create a subdirectory named after the video title converted to Pascal-kebab case (match existing examples):  
   - Example: `How I use Claude Code for real engineering` → `HowIUseClaudeCodeForRealEngineering`.
3. This directory will hold future assets (transcripts, screenshots, etc.). If the repo currently stores Markdown files directly under `youtube/`, keep doing so until a migration happens—just ensure the path matches `creators/{Creator}/youtube/{VideoTitle}.md`.

---

## 3. Create the Markdown Analysis File

1. Copy the template structure from `creators/Matt-Pocock/youtube/HowIUseClaudeCodeForRealEngineering.md`.
2. Update the metadata block:
   - **Video ID**
   - **Video URL**
   - **Title**
   - **Channel**
   - **Views** (use the value shown on YouTube at collection time)
   - **Upload Date** (MM/DD/YYYY)
3. Write the Summary (2–4 sentences referencing the video’s core claims, workflows, and audience takeaways).
4. Fill in the Comment Analysis section using ONLY comments that mention Cursor, Claude Code, Codex, Windsurf, or any other AI coding assistant (ignore everything else):
   - `Common Themes` must follow this exact order:  
     1. 2–3 sentence narrative summary of the filtered comments.  
     2. `Repeating themes:` list (pricing, speed, reliability, features, etc.).  
     3. `Criticisms:` bullet list calling out issues raised about AI coding tools.  
     4. `Praise:` bullet list for positive takes on AI coding tools.
   - `Notable Comments` table should contain 15–20 rows when possible, sorted by engagement (likes + replies), include the full untruncated comment text, date, and engagement numbers, omit author names, exclude any comments from the channel owner, and show only comments that reference the AI tools listed above.
5. Save the file as `/Users/liz/dev/cursor-research/creators/{Creator}/youtube/{VideoTitle}.md`.

### Markdown Snippet

````markdown
# {Video Title}
<img src="https://img.youtube.com/vi/{VideoID}/maxresdefault.jpg" alt="Video thumbnail" width="600" />

## Video Information

- **Video ID**: {VideoID}
- **Video URL**: https://www.youtube.com/watch?v={VideoID}
- **Title**: "{Video Title}"
- **Channel**: {Creator Name}
- **Views**: {View Count}
- **Upload Date**: {MM/DD/YYYY}

---

## Summary

{2-4 sentence summary}

---

## Comment Analysis

### Common Themes

{2-3 sentence summary of comments about Cursor/Claude Code/etc.}

**Repeating themes:** {comma-separated list}

**Criticisms:**
- {bulletized complaints about AI tools}

**Praise:**
- {bulletized positive remarks about AI tools}

### Notable Comments

| Comment | Date | Engagement |
|---------|------|------------|
| {Full comment text mentioning Cursor/Claude/etc.} | {MM/DD/YYYY} | {e.g., 12 👍, 3 💬} |
`````

#### Comment Analysis Rules Recap

- Capture only comments that name Cursor, Claude Code, Codex, Windsurf, or another AI coding tool.
- Aim for 15–20 rows; if fewer exist, note it directly under the table (e.g., “Only 9 qualifying comments available as of 11/15/2025.”).
- Sort by engagement (likes + replies) descending.
- Include the full comment text (no truncation), its posting date, and engagement numbers. Omit author names and skip any comment made by the creator’s own account.

---

## 4. Add the Video Info JSON

1. Use `yt-dlp --dump-json {YouTube URL}` (or YouTube Data API) to fetch raw metadata.
2. Save the JSON to `/Users/liz/dev/cursor-research/data/youtube-videos/{VideoID}.info.json`.
3. Keep the JSON unmodified except for removing transient download-specific paths if necessary.
4. Confirm the JSON includes at least: `id`, `title`, `uploader`, `upload_date`, `view_count`, `like_count`, `comment_count`, `description`, `thumbnails`.

---

## 5. Verification Checklist

- Directory: `creators/{Creator}/youtube/` exists and contains the Pascal-kebab Markdown file.
- Markdown mirrors the template and includes updated metadata, summary, and comments.
- JSON file lives in `data/youtube-videos/` and matches the `{VideoID}.info.json` naming convention.
- All paths, IDs, and dates match YouTube sources.

---

## 6. Commit Guidance

1. `git status` to review additions (expect one `.md` and one `.info.json`).
2. Commit message suggestion: `add {Creator} {VideoID} analysis`.
3. Push or draft PR as usual.

---

## FAQs

- **Q: What if the creator already has multiple videos?**  
  A: Reuse the same `creators/{Creator}/youtube/` directory; add another Markdown file per video.

- **Q: How strict is the title casing for directories?**  
  A: Follow existing pattern exactly; look at neighboring files for reference before creating new ones.

- **Q: Do I have to watch the entire video?**  
  A: At minimum, skim the transcript and key segments plus top comments to ensure accuracy.

- **Q: Where do transcripts or screenshots go?**  
  A: Place auxiliary assets inside the video’s subdirectory (e.g., `creators/{Creator}/youtube/{VideoTitle}/assets/`) if needed in the future.

---

Following this script produces the three artifacts the requester expects: the creator/video directory, the formatted Markdown analysis, and the synced JSON metadata file. Use it verbatim whenever onboarding a new YouTube video into the analysis repo.

