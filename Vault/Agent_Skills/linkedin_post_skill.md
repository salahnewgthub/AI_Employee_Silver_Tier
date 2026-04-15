# Agent Skill: LinkedIn Post — Sales Generation

## Trigger
When a LINKEDIN_draft_request file appears in /Needs_Action

## Your Goal
Write a compelling LinkedIn post that generates business interest and
leads and when the post is written then read aloud complete post. The post should feel human, valuable, and non-spammy.

## Steps
1. Read Business_Goals.md to understand the business and current goals
2. Read Company_Handbook.md for tone and rules
3. Choose one of these proven post formats (rotate them):
   - **Problem → Solution**: Describe a pain point your audience has,
     then explain how you solve it
   - **Insight / Tip**: Share a genuinely useful tip from your industry
   - **Story**: Short story about a client win or lesson learned
   - **Question**: Ask a thought-provoking question relevant to your niche
4. Write the post following the rules below
5. Save to /Pending_Approval/LINKEDIN_post_[YYYY-MM-DD].md
6. Update Dashboard.md: note post is pending approval
7. Move the request file from /Needs_Action to /Done

## Post Writing Rules
- Length: 150–280 words (LinkedIn's sweet spot for engagement)
- Start with a STRONG first line (no "I am excited to share...")
- Use short paragraphs — 1 to 2 sentences each
- Add 3 to 5 relevant hashtags at the end
- End with a soft call to action (e.g. "DM me if you'd like to explore this")
- NO corporate jargon, NO emojis unless very sparing
- Sound like a real human expert, not a marketing bot

## Output Format
Save the file as:
/Pending_Approval/LINKEDIN_post_[date].md

With this exact structure:
---
type: linkedin_post
created: [timestamp]
status: pending_approval
char_count: [count]
format_used: [problem-solution / insight / story / question]
---

## Draft LinkedIn Post

[post text here — this is what gets copied and posted]

---
Move this file to /Approved to post, or /Rejected to discard.