# Agent Skill: Daily Briefing

## Trigger
Scheduled — runs every morning at 8:00 AM

## Steps
1. Read all files in /Needs_Action
2. Read Dashboard.md
3. Read Business_Goals.md
4. Count items by category (emails, whatsapp, linkedin)
5. Write a Monday Morning Briefing to /Briefings/[date]_Briefing.md
6. Update Dashboard.md with briefing summary

## Output Format
# Morning Briefing — [Date]

## Summary
- Pending emails: X
- Pending WhatsApp messages: X
- Items needing approval: X

## Top Priority
[Most urgent item]

## Suggested Actions
[Claude's recommendations]
```

---

## 🐍 PHASE 4 — Create the Python Watcher Scripts

Now you'll create the Python scripts that "watch" Gmail, WhatsApp, and LinkedIn. Open VSCode's integrated terminal: go to **Terminal → New Terminal** in VSCode.

First, install the Python packages you need:
```
cd E:\AI_Employee_Silver_Tier
pip install google-auth google-auth-oauthlib google-api-python-client watchdog playwright python-dotenv
playwright install chromium
```

**Step 4.1 — Create the `.env` file (credentials — never share this)**

Create `E:\AI_Employee_Silver_Tier\.env`:
```
# Gmail API credentials
GMAIL_CREDENTIALS_PATH=E:\AI_Employee_Silver_Tier\credentials\gmail_token.json
VAULT_PATH=E:\AI_Employee_Silver_Tier\Vault

# Safety setting — keep as true during testing!
DRY_RUN=true

# WhatsApp session
WHATSAPP_SESSION_PATH=E:\AI_Employee_Silver_Tier\whatsapp_session
```

Create `E:\AI_Employee_Silver_Tier\.gitignore`:
```
.env
credentials/
whatsapp_session/
*.pyc
__pycache__/