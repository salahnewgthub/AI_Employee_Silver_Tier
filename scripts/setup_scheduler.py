"""
Setup Windows Task Scheduler entries for the AI Employee.

Creates recurring tasks:
  1. Daily Briefing — runs every morning at 8:00 AM
  2. Orchestrator Heartbeat — runs every 15 minutes to ensure orchestrator is alive
  3. LinkedIn Draft Check — runs every 2 days at 9:00 AM

Run as Administrator: python setup_scheduler.py
"""

import subprocess
import sys
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
VAULT_PATH = SCRIPT_DIR / "Vault"
PYTHON_EXE = sys.executable

TASKS = [
    {
        "name": "AI_Employee_Daily_Briefing",
        "description": "Generate a morning briefing from the AI Employee vault every day at 8:00 AM",
        "trigger": "DAILY",
        "start_time": "08:00",
        "action": f'"{PYTHON_EXE}" "{SCRIPT_DIR}\\scripts\\claude_vault.py" --briefing',
        "start_in": str(VAULT_PATH),
        "run_level": "HIGHEST",
    },
    {
        "name": "AI_Employee_Orchestrator_Heartbeat",
        "description": "Ensure the AI Employee Orchestrator is running every 15 minutes",
        "trigger": "MINUTE",
        "interval": "15",
        "action": f'"{PYTHON_EXE}" "{SCRIPT_DIR}\\scripts\\orchestrator.py"',
        "start_in": str(SCRIPT_DIR),
        "run_level": "HIGHEST",
    },
    {
        "name": "AI_Employee_Linkedin_Draft",
        "description": "Check for new LinkedIn draft requests every 2 days at 9:00 AM",
        "trigger": "DAILY",
        "start_time": "09:00",
        "modifier": "2",
        "action": f'"{PYTHON_EXE}" "{SCRIPT_DIR}\\scripts\\linkedin_watcher.py"',
        "start_in": str(SCRIPT_DIR),
        "run_level": "HIGHEST",
    },
]


def task_exists(task_name: str) -> bool:
    """Check if a scheduled task already exists."""
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", task_name],
            capture_output=True, text=True, check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def delete_task(task_name: str):
    """Delete a scheduled task."""
    try:
        subprocess.run(
            ["schtasks", "/delete", "/tn", task_name, "/f"],
            capture_output=True, text=True, check=False
        )
        print(f"  Deleted existing task: {task_name}")
    except Exception as e:
        print(f"  Warning: Could not delete task {task_name}: {e}")


def create_task(task: dict) -> bool:
    """Create a Windows Scheduled Task."""
    name = task["name"]

    if task_exists(name):
        print(f"  Task already exists: {name}")
        print(f"  → Skipping. To recreate, first run: python setup_scheduler.py --recreate")
        return False

    cmd = ["schtasks", "/create", "/tn", name, "/tr", task["action"], "/sc"]

    trigger = task["trigger"]
    if trigger == "DAILY":
        cmd.append("daily")
        cmd.extend(["/st", task["start_time"]])
        if task.get("modifier"):
            cmd.extend(["/mo", task["modifier"]])
    elif trigger == "MINUTE":
        cmd.append("minute")
        cmd.extend(["/mo", task.get("interval", "15")])
    elif trigger == "HOURLY":
        cmd.append("hourly")
        cmd.extend(["/mo", task.get("interval", "1")])

    cmd.extend(["/sd", "01/01/2026"])  # Start date
    cmd.extend(["/f"])  # Force create

    if task.get("run_level") == "HIGHEST":
        cmd.extend(["/rl", "HIGHEST"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"  ✅ Created task: {name}")
            return True
        else:
            print(f"  ❌ Failed to create task: {name}")
            err = result.stderr.strip()
            if "Access is denied" in err:
                print(f"     ⚠️  ERROR: Run this script as Administrator!")
                print(f"     Right-click Command Prompt → 'Run as administrator'")
                print(f"     Then run: python scripts\\setup_scheduler.py")
            else:
                print(f"     Error: {err}")
            return False
    except FileNotFoundError:
        print(f"  ❌ Error: schtasks.exe not found. Run this script as Administrator.")
        return False
    except Exception as e:
        print(f"  ❌ Error creating task {name}: {e}")
        return False


def list_ai_employee_tasks():
    """List all AI Employee scheduled tasks."""
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "LIST", "/v"],
            capture_output=True, text=True, check=False
        )
        tasks = result.stdout.split("\r\n")
        ai_tasks = []
        for i, line in enumerate(tasks):
            if "AI_Employee" in line:
                # Collect this task and next few lines
                ai_tasks.append(line)
                for j in range(1, 6):
                    if i + j < len(tasks):
                        ai_tasks.append(tasks[i + j])

        if ai_tasks:
            print("\n📋 Current AI Employee Scheduled Tasks:")
            print("-" * 50)
            print("\n".join(ai_tasks))
            print("-" * 50)
        else:
            print("  No AI Employee scheduled tasks found.")
    except Exception as e:
        print(f"  Could not list tasks: {e}")


def main():
    recreate = "--recreate" in sys.argv

    print("=" * 60)
    print("  AI Employee — Windows Task Scheduler Setup")
    print("=" * 60)
    print()

    if recreate:
        print("⚠️  Recreate mode: Deleting existing tasks first...\n")
        for task in TASKS:
            if task_exists(task["name"]):
                delete_task(task["name"])

    print(f"Creating {len(TASKS)} scheduled tasks:\n")

    created = 0
    for task in TASKS:
        print(f"📝 Task: {task['name']}")
        print(f"   Description: {task['description']}")
        if task["trigger"] == "DAILY":
            modifier = f" (every {task.get('modifier', '1')} day(s))" if task.get("modifier") and task["modifier"] != "1" else ""
            print(f"   Schedule: Daily at {task['start_time']}{modifier}")
        elif task["trigger"] == "MINUTE":
            print(f"   Schedule: Every {task.get('interval', '15')} minutes")
        print(f"   Command: {task['action']}")
        print()

        if create_task(task):
            created += 1
        print()

    print("=" * 60)
    print(f"  {created}/{len(TASKS)} tasks created successfully")
    print("=" * 60)
    print()

    print("ℹ️  To manage tasks:")
    print("   • Open Task Scheduler (Win+R → taskschd.msc)")
    print("   • Look for tasks starting with 'AI_Employee_*'")
    print("   • You can enable/disable/edit them there")
    print()

    print("ℹ️  To verify all tasks:")
    print("   • Run: python scripts\\setup_scheduler.py --list")
    print()

    if "--list" in sys.argv:
        list_ai_employee_tasks()


if __name__ == "__main__":
    main()
