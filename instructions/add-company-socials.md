# Add AI Company Social Media Research

This playbook walks you through adding research on an AI company's social media accounts (TikTok, Instagram, and X/Twitter) to the repo. Follow the steps in order to ensure consistency with existing conventions.

---

## 1. Collect Input

1. Get the company name (e.g., "Anthropic", "OpenAI", "Cursor").
2. Identify the company directory name (kebab case, e.g., `anthropic`, `openai`, `cursor`).
3. Collect the following information for each platform:
   - **TikTok**: Account URL/username, follower count, and video/post count
   - **Instagram**: Account URL/username, follower count, and post count
   - **X (Twitter)**: Account URL/username, follower count, and tweet/post count

---

## 2. Create Directory Structure

1. Confirm the company directory exists at `/Users/liz/dev/cursor-research/ai-companies/{company-name}/`.  
   - If missing, create it (including intermediate folders).
2. Create the `socials.md` file at `/Users/liz/dev/cursor-research/ai-companies/{company-name}/socials.md`.

---

## 3. Create socials.md File

Create a markdown file at `/Users/liz/dev/cursor-research/ai-companies/{company-name}/socials.md` with the following structure:

### Markdown Template

````markdown
# {Company Name} Social Media Accounts

## Overview

- **TikTok**: [{@username}]({tiktok_url}) - {follower_count} followers
- **Instagram**: [{@username}]({instagram_url}) - {follower_count} followers
- **X (Twitter)**: [{@username}]({x_url}) - {follower_count} followers

---

**Last Updated**: {MM/DD/YYYY}
````

### Section Details

1. **Overview Section**:
   - Each platform should be listed as a bullet point
   - Platform name should be bold
   - Username should be hyperlinked to the account URL
   - Follower count should be formatted with commas (e.g., "1,234,567")
   - If a platform account doesn't exist, write "N/A" for both the link and follower count

2. **Last Updated**:
   - Date when the data was collected (MM/DD/YYYY format)

---

## 4. Finding Social Media Accounts

### TikTok
- Search for the company name on TikTok
- Look for verified accounts (blue checkmark)
- Common URL format: `https://www.tiktok.com/@username`
- Follower count is displayed on the profile page

### Instagram
- Search for the company name on Instagram
- Look for verified accounts (blue checkmark)
- Common URL format: `https://www.instagram.com/username/`
- Follower count is displayed on the profile page

### X (Twitter)
- Search for the company name on X/Twitter
- Look for verified accounts (blue checkmark)
- Common URL format: `https://x.com/username` or `https://twitter.com/username`
- Follower count is displayed on the profile page

---

## 5. Update README Table

After successfully creating the `socials.md` file, update the main README table to include the new company:

1. Open `/Users/liz/dev/cursor-research/ai-companies/readme.md`
2. Locate the "Company Social Accounts" table
3. Extract the following information from the newly created `socials.md` file's Overview section:
   - **X (Twitter)**: Follower count (with commas, e.g., "1,234,567")
   - **Instagram**: Follower count (with commas)
   - **TikTok**: Follower count (with commas)
4. Add a new row to the table with:
   - Company name hyperlinked to `{company-name}/socials.md`
   - X follower count (or "N/A" if account doesn't exist)
   - Instagram follower count (or "N/A" if account doesn't exist)
   - TikTok follower count (or "N/A" if account doesn't exist)
5. Keep the table sorted alphabetically by company name

**Example:**
If you just added "Example Company" with 100,000 X followers, 75,000 Instagram followers, and 50,000 TikTok followers, add this row (in alphabetical order):

```markdown
| [Example Company](example-company/socials.md) | 100,000 | 75,000 | 50,000 |
```

---

## 6. Verification Checklist

- [ ] Directory `ai-companies/{company-name}/` exists
- [ ] `socials.md` file exists at the correct path
- [ ] All three platforms (TikTok, Instagram, X) are included in the file
- [ ] All account URLs are valid and hyperlinked correctly
- [ ] Follower counts are formatted with commas
- [ ] Post counts are included and formatted with commas
- [ ] If a platform account doesn't exist, "N/A" is used appropriately
- [ ] Last updated date is included in the file
- [ ] Date format is MM/DD/YYYY
- [ ] README table at `ai-companies/readme.md` has been updated with the new company's social media statistics
- [ ] Company row in README table is in alphabetical order

---

## 7. Commit Guidance

1. `git status` to review additions (expect `socials.md` file and updated `readme.md`).
2. Commit message suggestion: `add {company-name} social media research`.
3. Push or draft PR as usual.

---

## 8. Example

For a company called "Example AI" with:
- TikTok: @exampleai (50,000 followers)
- Instagram: @exampleai (75,000 followers)
- X: @exampleai (100,000 followers)

**socials.md**:
````markdown
# Example AI Social Media Accounts

## Overview

- **TikTok**: [@exampleai](https://www.tiktok.com/@exampleai) - 50,000 followers
- **Instagram**: [@exampleai](https://www.instagram.com/exampleai/) - 75,000 followers
- **X (Twitter)**: [@exampleai](https://x.com/exampleai) - 100,000 followers

---

**Last Updated**: 12/15/2024
````

**README table update** (add this row to `ai-companies/readme.md` in the "Company Social Accounts" table, in alphabetical order):

```markdown
| [Example AI](example-ai/socials.md) | 100,000 | 75,000 | 50,000 |
```

---

## 9. FAQs

- **Q: What if a company doesn't have an account on one of the platforms?**  
  A: Use "N/A" for both the account link and follower count in the file.

- **Q: How do I find the exact follower count?**  
  A: Visit the platform's profile page. The follower count is typically displayed prominently. Note that follower counts change frequently, so record the count at the time of data collection.

- **Q: What if the company has multiple accounts (e.g., different regional accounts)?**  
  A: Use the main/primary account for the company. If there's a clear main account (usually verified and with the company name), use that one.

- **Q: Should I update follower counts regularly?**  
  A: Update the "Last Updated" date whenever you refresh the follower counts and post counts. Consider setting a schedule (e.g., monthly) to keep data current.

- **Q: How do I update the README table?**  
  A: Extract the follower counts from the `socials.md` file's Overview section. Add a new row with the company name hyperlinked to `{company-name}/socials.md`, followed by the three follower counts (X, Instagram, TikTok) in that order. Keep the table sorted alphabetically by company name.

---

Following this playbook produces comprehensive social media research files for AI companies. Use it whenever adding social media information for a company in the analysis repo.

