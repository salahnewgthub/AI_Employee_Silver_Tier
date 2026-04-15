#!/usr/bin/env python3
"""
vault_cli.py - Command-line interface for AI Employee Vault operations.

Usage:
    python scripts/vault_cli.py list [directory]
    python scripts/vault_cli.py read <file>
    python scripts/vault_cli.py create <file> [--content "text"]
    python scripts/vault_cli.py move <source> <dest>
    python scripts/vault_cli.py claude "<prompt>" [--action write]
    python scripts/vault_cli.py status
    python scripts/vault_cli.py dashboard
    python scripts/vault_cli.py plan [--briefing]
    python scripts/vault_cli.py process
    python scripts/vault_cli.py help

Examples:
    python scripts/vault_cli.py list Needs_Action
    python scripts/vault_cli.py read Needs_Action/test_manual.md
    python scripts/vault_cli.py status
    python scripts/vault_cli.py claude "Create a summary of all pending items" --action write
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime

# Vault paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
VAULT_PATH = ROOT_DIR / "Vault"
LOGS_DIR = VAULT_PATH / "Logs"
DASHBOARD_PATH = VAULT_PATH / "Dashboard.md"

# Vault directories
VAULT_DIRS = [
    "Inbox", "Needs_Action", "Pending_Approval", "Approved", 
    "Done", "Rejected", "Plans", "Briefings", "Logs", "Agent_Skills"
]

def log_action(message):
    """Log an action with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def cmd_list(directory=None):
    """List files in a vault directory."""
    if directory:
        target = VAULT_PATH / directory
        if not target.exists():
            print(f"❌ Directory not found: {directory}")
            return False
    else:
        target = VAULT_PATH
        directory = "Vault"
    
    print(f"📁 Contents of {directory}/")
    print("-" * 60)
    
    files = sorted(target.iterdir())
    if not files:
        print("  (empty)")
        return True
    
    for item in files:
        if item.is_dir():
            subdir_files = len(list(item.glob("*")))
            print(f"  📂 {item.name}/  ({subdir_files} items)")
        else:
            size = item.stat().st_size
            modified = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"  📄 {item.name}  ({size} bytes, {modified})")
    
    print(f"\n✅ Total: {len(files)} items in {directory}/")
    return True

def cmd_read(file_path):
    """Read and display a file's contents."""
    target = VAULT_PATH / file_path
    if not target.exists():
        # Try with Needs_Action prefix
        target = VAULT_PATH / "Needs_Action" / file_path
    
    if not target.exists():
        print(f"❌ File not found: {file_path}")
        print(f"Available in Needs_Action/:")
        for f in (VAULT_PATH / "Needs_Action").glob("*"):
            print(f"  - {f.name}")
        return False
    
    print(f"📄 Reading: {target.relative_to(VAULT_PATH)}")
    print("-" * 60)
    
    content = target.read_text(encoding="utf-8")
    print(content)
    
    return True

def cmd_create(file_path, content=None):
    """Create a new file in the vault."""
    target = VAULT_PATH / file_path
    target.parent.mkdir(parents=True, exist_ok=True)
    
    if content is None:
        print(f"📝 Creating empty file: {file_path}")
        target.touch()
    else:
        print(f"📝 Creating file: {file_path}")
        target.write_text(content, encoding="utf-8")
    
    log_action(f"Created {file_path}")
    update_dashboard(f"Created {file_path}")
    return True

def cmd_move(source, dest):
    """Move a file within the vault."""
    src = VAULT_PATH / source
    dst = VAULT_PATH / dest
    
    if not src.exists():
        print(f"❌ Source file not found: {source}")
        return False
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    
    print(f"✅ Moved: {source} → {dest}")
    log_action(f"Moved {source} → {dest}")
    update_dashboard(f"Moved {source} → {dest}")
    return True

def cmd_claude(prompt, action="none"):
    """Run Claude on a prompt and optionally execute file writes."""
    print(f"🤖 Running Claude with prompt...")
    print(f"Prompt: {prompt}")
    print("-" * 60)
    
    # Use claude_vault.py which handles file writes
    vault_cli = SCRIPT_DIR / "claude_vault.py"
    
    if action == "write" or "create" in prompt.lower() or "plan" in prompt.lower():
        # Run through claude_vault.py to handle file creation
        cmd = f'python "{vault_cli}" "{prompt}"'
    else:
        # Just get Claude's response
        cmd = f'cd /d "{VAULT_PATH}" && claude -p "{prompt}" --dangerously-skip-permissions'
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=300,
        encoding='utf-8',
        errors='ignore'
    )
    
    output = (result.stdout or '') + (result.stderr or '')
    
    # Print Claude's response
    if output:
        print(output)
    else:
        print("(No output from Claude)")
    
    if result.returncode != 0:
        print(f"\n⚠️  Claude exited with code {result.returncode}")
    
    return True

def cmd_status():
    """Show vault status overview."""
    print("📊 AI Employee Vault Status")
    print("=" * 60)
    
    for dirname in VAULT_DIRS:
        dir_path = VAULT_PATH / dirname
        if dir_path.exists():
            files = list(dir_path.glob("*"))
            status = "✅" if files else "📁"
            print(f"{status} {dirname:20s} ({len(files)} items)")
            
            # Show recent files for key directories
            if dirname in ["Needs_Action", "Approved", "Pending_Approval"] and files:
                for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                    modified = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d %H:%M")
                    print(f"     └─ {f.name}  ({modified})")
        else:
            print(f"❌ {dirname:20s} (missing)")
    
    print()
    
    # Show Dashboard summary
    if DASHBOARD_PATH.exists():
        content = DASHBOARD_PATH.read_text(encoding="utf-8")
        for line in content.split("\n")[:10]:
            if line.strip():
                print(f"   {line}")
    
    return True

def cmd_dashboard():
    """Display the full Dashboard."""
    if not DASHBOARD_PATH.exists():
        print("❌ Dashboard.md not found")
        return False
    
    print("📊 AI Employee Dashboard")
    print("=" * 60)
    print(DASHBOARD_PATH.read_text(encoding="utf-8"))
    return True

def cmd_plan(briefing=False):
    """Create a plan file."""
    vault_cli = SCRIPT_DIR / "claude_vault.py"
    
    if briefing:
        cmd = f'python "{vault_cli}" --briefing'
    else:
        cmd = f'python "{vault_cli}" "Create a Plan.md based on files in Needs_Action"'
    
    print(f"📋 Creating plan...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    output = (result.stdout or '') + (result.stderr or '')
    print(output)
    
    return True

def cmd_process():
    """Process all files in Needs_Action."""
    needs_action = VAULT_PATH / "Needs_Action"
    files = list(needs_action.glob("*.md"))
    
    if not files:
        print("✅ No files to process in Needs_Action/")
        return True
    
    print(f"📂 Processing {len(files)} file(s) in Needs_Action/")
    print("-" * 60)
    
    processed = 0
    for f in sorted(files):
        content = f.read_text(encoding="utf-8")
        
        # Parse frontmatter
        file_type = "unknown"
        skill = "unknown"
        if content.startswith("---"):
            lines = content.split("\n")
            in_fm = False
            metadata = {}
            for line in lines:
                if line.strip() == "---":
                    if not in_fm:
                        in_fm = True
                    else:
                        break
                elif in_fm and ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
            
            file_type = metadata.get("type", "unknown")
            skill = metadata.get("skill", "unknown")
        
        print(f"📄 {f.name}")
        print(f"   Type: {file_type}, Skill: {skill}")
        
        # Determine action based on type
        if file_type == "test":
            print(f"   → Test file")
            print(f"   ✅ Action: Use 'vault_cli.py plan --briefing' to create briefing")
        elif file_type == "email":
            print(f"   → Email requiring response")
            dest = f"Pending_Approval/{f.name}"
            cmd_move(str(f.relative_to(VAULT_PATH)), dest)
        elif file_type == "linkedin_draft_request":
            print(f"   → LinkedIn draft request")
            print(f"   ✅ Action: Run 'python scripts\\linkedin_watcher.py' to create draft")
        elif file_type == "whatsapp":
            print(f"   → WhatsApp message")
            print(f"   ✅ Action: Review message content and respond if needed")
        elif file_type == "file_drop":
            print(f"   → Dropped file")
            print(f"   ✅ Action: Review and move to appropriate folder")
        else:
            print(f"   → Unknown type")
            print(f"   ✅ Action: Review manually and take appropriate action")
        
        processed += 1
        print()
    
    print(f"✅ Processed {processed} file(s)")
    print(f"💡 Tip: Use 'vault_cli.py claude \"<prompt>\" --action write' for Claude tasks")
    
    return True

def update_dashboard(action_description):
    """Update Dashboard.md with an activity entry."""
    if not DASHBOARD_PATH.exists():
        return False
    
    content = DASHBOARD_PATH.read_text(encoding="utf-8")
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %I:%M %p")
    log_entry = f"- {timestamp} — {action_description}"
    
    import re
    # Update Last Updated timestamp
    content = re.sub(r'Last Updated: .+', f'Last Updated: {timestamp}', content)
    
    # Add to Recent Activity
    if "## Recent Activity" in content:
        content = content.replace(
            "## Recent Activity\n",
            f"## Recent Activity\n{log_entry}\n"
        )
    else:
        content += f"\n## Recent Activity\n{log_entry}\n"
    
    DASHBOARD_PATH.write_text(content, encoding="utf-8")
    return True

def cmd_help():
    """Show help."""
    print("🤖 AI Employee Vault CLI")
    print("=" * 60)
    print()
    print("Commands:")
    print("  list [directory]       List files in vault directory")
    print("  read <file>            Read file contents")
    print("  create <file>          Create new file")
    print("  move <src> <dest>      Move file within vault")
    print("  claude \"<prompt>\"      Run Claude with a prompt")
    print("  status                 Show vault overview")
    print("  dashboard              Display Dashboard.md")
    print("  plan [--briefing]      Create Plan.md")
    print("  process                Process all Needs_Action files")
    print("  help                   Show this help")
    print()
    print("Examples:")
    print('  python scripts/vault_cli.py list Needs_Action')
    print('  python scripts/vault_cli.py read Needs_Action/test_manual.md')
    print('  python scripts/vault_cli.py status')
    print('  python scripts/vault_cli.py claude "Summarize all pending items"')
    print('  python scripts/vault_cli.py process')
    return True

def main():
    if len(sys.argv) < 2:
        cmd_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        "list": lambda: cmd_list(sys.argv[2] if len(sys.argv) > 2 else None),
        "read": lambda: cmd_read(sys.argv[2]) if len(sys.argv) > 2 else (print("❌ Usage: vault_cli.py read <file>"), False),
        "create": lambda: cmd_create(sys.argv[2], " ".join(sys.argv[4:]) if "--content" in sys.argv else None),
        "move": lambda: cmd_move(sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else (print("❌ Usage: vault_cli.py move <source> <dest>"), False),
        "claude": lambda: cmd_claude(" ".join(sys.argv[2:]), "write" if "--action" in sys.argv else "none"),
        "status": cmd_status,
        "dashboard": cmd_dashboard,
        "plan": lambda: cmd_plan("--briefing" in sys.argv),
        "process": cmd_process,
        "help": cmd_help,
    }
    
    if command in commands:
        success = commands[command]()
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        cmd_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
