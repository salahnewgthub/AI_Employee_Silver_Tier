# AI Employee Vault - Claude Instructions

## CRITICAL: Command Execution Limitation
**This model cannot see command outputs.** When you output bash commands, they are displayed but you don't receive the results. 

**WORKAROUND:** Instead of running commands, read files directly using the MCP filesystem tools:
- Use `read_file` to read file contents
- Use `read_directory` to list folder contents
- Use `write_file` to create/modify files

**Example of what NOT to do:**
```
ls Needs_Action/  # This won't show you results!
```

**Example of what TO do:**
```
read_file(path="Needs_Action/test_manual.md")
```

If you need to list files, explicitly state: "I need to use read_directory on Needs_Action folder" and the system will handle it.

## Environment
- OS: Windows with WSL available
- Working directory: `E:\AI_Employee_Silver_Tier\Vault`
- MCP filesystem tools ARE available and working
- WSL path for files: `/mnt/e/AI_Employee_Silver_Tier/Vault/`

## Available MCP Tools
- `read_file(path)` - Read file contents
- `read_directory(path)` - List directory contents  
- `write_file(path, content)` - Create/write files
- `edit_file(path, changes)` - Edit existing files
- `search_files(pattern)` - Find files by pattern

## Vault Structure
```
Vault/
├── Inbox/              # Drop files here for processing
├── Needs_Action/       # Items requiring Claude action
│   ├── test_manual.md
│   ├── EMAIL_20260411_123822_19d7b78b.md
│   ├── FILE_20260413_181900_test_file_005.md
│   ├── LINKEDIN_draft_request_20260413_181407.md
│   └── WHATSAPP_20260412_101342.md
├── Pending_Approval/   # Drafts awaiting human approval
├── Approved/           # Approved items ready for execution
├── Done/               # Completed actions
├── Rejected/           # Rejected items
├── Plans/              # Plan.md files created by Claude
│   └── Plan.md
├── Briefings/          # Daily briefing outputs
├── Logs/               # System logs and screenshots
├── Agent_Skills/       # Skill definitions
├── Dashboard.md        # Main status dashboard
├── Company_Handbook.md # Rules and guidelines
└── Business_Goals.md   # Company objectives
```

## Workflow Rules
1. When files appear in `/Needs_Action/`, read them and create a `Plan.md` in `/Plans/`
2. If action requires human approval, write to `/Pending_Approval/`
3. Check `/Approved/` for items ready to execute
4. Move completed files to `/Done/`
5. Update `Dashboard.md` after each action

## Key Files
- `Dashboard.md` - Current status, update after actions
- `Company_Handbook.md` - Communication rules, priority keywords
- `Business_Goals.md` - Company objectives for context
