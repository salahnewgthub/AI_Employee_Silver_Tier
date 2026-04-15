# Agent Skill: Process Email

## Trigger
When a file appears in /Needs_Action with type: email

## Steps
1. Read the email file from /Needs_Action
2. Classify: is this urgent, routine, or spam?
3. If urgent: create a Plan.md in /Plans with response steps
4. Draft a reply in /Pending_Approval/EMAIL_reply_[id].md
5. Update Dashboard.md with the new item
6. Do NOT send the email — wait for human approval

## Output Format for Approval File
---
type: email_reply
to: [recipient]
subject: [subject]
body: [draft body]
status: pending
---
Move this file to /Approved to send, or /Rejected to discard.