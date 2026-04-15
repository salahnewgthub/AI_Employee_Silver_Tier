# Morning Briefing Plan

**Source:** Needs_Action/test_manual.md
**Skill:** daily_briefing_skill
**Created:** 2026-04-14

---

## 1) Objective
Create a comprehensive daily morning briefing that provides executives with a concise, accurate, and timely overview of critical business information. The briefing must be delivered before 9 AM and formatted for quick executive consumption.

## 2) Data to Gather
- **System Health Status** — status of all critical systems and services
- **Critical Alerts & Incidents** — urgent issues from alert systems requiring attention
- **Key Performance Metrics** — KPIs and business indicators from dashboards
- **Market Updates** — relevant news and market movements from filtered feeds
- **Pending Executive Tasks** — items requiring decision or action from project management
- **Strategic Initiatives Progress** — updates on major company projects
- **Unread Communications** — flagged emails, WhatsApp messages, and LinkedIn activity from Vault/Needs_Action

## 3) Structure
1. **Executive Summary** — 1-2 sentences highlighting the most critical items
2. **System Health** — color-coded status (Red/Yellow/Green)
3. **Critical Alerts** — incidents requiring immediate attention
4. **Performance Metrics** — key numbers with trend context
5. **Market Intelligence** — relevant external updates
6. **Action Items** — tasks requiring executive decisions
7. **Communication Summary** — summary of unread emails/messages from watchers

## 4) Output Format
- **Primary:** Markdown file saved to `Vault/Briefings/briefing_YYYY-MM-DD.md`
- **Distribution:** Email to executives (via Gmail MCP when configured)
- **Dashboard:** Posted to `Vault/Dashboard.md` under Recent Activity
- **Mobile-friendly:** Bullet points, short sections, no dense paragraphs

## 5) Execution Steps
1. Read `Vault/Needs_Action/` for pending items requiring attention
2. Read `Vault/Dashboard.md` for current status context
3. Read `Vault/Company_Handbook.md` for communication rules and priority keywords
4. Compile briefing sections based on gathered data
5. Write briefing file to `Vault/Briefings/briefing_YYYY-MM-DD.md`
6. Update `Vault/Dashboard.md` with briefing completion status

---

## Status: Ready for Execution
