# AI Employee Vault CLI Guide

## Quick Start

```bat
REM Show all files in vault
vault status

REM List files in a directory
vault list Needs_Action

REM Read a file
vault read Needs_Action/test_manual.md

REM Process all pending items
vault process

REM Create a morning briefing plan
vault plan --briefing

REM Run Claude on a task
vault claude "Summarize all pending items" --action write
```

## All Commands

| Command | Description | Example |
|---------|-------------|---------|
| `vault status` | Show vault overview with file counts | `vault status` |
| `vault list [dir]` | List files in a directory | `vault list Needs_Action` |
| `vault read <file>` | Read file contents | `vault read test_manual.md` |
| `vault create <file>` | Create a new file | `vault create Plans/test.md` |
| `vault move <src> <dest>` | Move file within vault | `vault move Needs_Action/file.md Approved/file.md` |
| `vault claude "<prompt>"` | Run Claude with a prompt | `vault claude "Create summary" --action write` |
| `vault dashboard` | Display Dashboard.md | `vault dashboard` |
| `vault plan [--briefing]` | Create Plan.md | `vault plan --briefing` |
| `vault process` | Process all Needs_Action files | `vault process` |
| `vault help` | Show help | `vault help` |

## Why Use This CLI?

The local model (`if/qwen3-coder-plus`) has a **limitation**: it cannot execute file operations or see command results when run interactively with `claude`.

**This CLI works around that by:**
1. ✅ Running Claude in the background
2. ✅ Executing file operations directly via Python
3. ✅ Updating Dashboard.md automatically
4. ✅ Handling encoding issues properly

## Workflow Examples

### 1. Morning Briefing
```bat
vault plan --briefing
```

### 2. Process New Emails
```bat
vault process
```

### 3. Move Email to Approved
```bat
vault move Pending_Approval/EMAIL_xxx.md Approved/EMAIL_xxx.md
```

### 4. Check Status
```bat
vault status
```

### 5. Create Custom Plan
```bat
vault claude "Create a plan for processing WhatsApp messages" --action write
```

## Notes

- **Interactive Claude** (`claude`) is good for simple Q&A but **cannot do file operations**
- **Vault CLI** handles all file operations reliably
- All CLI commands update `Dashboard.md` automatically
- Files moved to `Approved/` trigger the orchestrator's approval workflow
