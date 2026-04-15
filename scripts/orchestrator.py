import os
import sys
import subprocess
import time
import threading
import logging
import atexit
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

VAULT_PATH = Path(os.getenv("VAULT_PATH", r"E:\AI_Employee_Silver_Tier\Vault"))
SCRIPTS_DIR = Path(__file__).parent
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# ── Singleton lock: prevent multiple orchestrator instances ─────────────
PID_FILE = Path(__file__).parent.parent / "logs" / "orchestrator.pid"

def acquire_lock():
    """Ensure only one orchestrator instance runs at a time."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            # Check if old process is still alive
            os.kill(old_pid, 0)
            logger.warning(f"Another orchestrator is running (PID {old_pid}). Exiting.")
            sys.exit(1)
        except (ProcessLookupError, ValueError):
            # Old process is dead — stale PID file
            logger.info("Stale PID file found. Cleaning up.")
            PID_FILE.unlink()
    PID_FILE.write_text(str(os.getpid()))
    logger.info(f"Orchestrator lock acquired (PID {os.getpid()})")

def release_lock():
    """Remove the PID lock file on exit."""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
            logger.info("Orchestrator lock released.")
    except Exception as e:
        logger.debug(f"Could not remove PID file: {e}")

atexit.register(release_lock)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Orchestrator] %(levelname)s: %(message)s"
)
logger = logging.getLogger("Orchestrator")

def run_script_in_thread(script_name: str, restart_on_exit=True):
    """Run a watcher script as a background thread."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        logger.warning(f"Script not found: {script_path}")
        return
    def target():
        while True:
            try:
                logger.info(f"Starting {script_name}")
                result = subprocess.run(["python", str(script_path)], check=False)
                if not restart_on_exit:
                    logger.info(f"{script_name} completed (exit code {result.returncode}), not restarting")
                    break
                if result.returncode != 0:
                    logger.error(f"{script_name} crashed (exit code {result.returncode}). Restarting in 30s...")
                    time.sleep(30)
                else:
                    logger.info(f"{script_name} exited cleanly. Restarting in 30s...")
                    time.sleep(30)
            except Exception as e:
                logger.error(f"{script_name} crashed: {e}. Restarting in 30s...")
                time.sleep(30)
    t = threading.Thread(target=target, daemon=True, name=script_name)
    t.start()
    return t

def trigger_claude(prompt: str):
    """Trigger Claude Code to process the vault."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would trigger Claude with: {prompt}")
        return
    vault = str(VAULT_PATH)
    # cd into vault dir then run claude (no --cwd flag available)
    cmd = f'cd /d "{vault}" && claude -p "{prompt}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
        if result.stdout:
            logger.info(f"Claude output: {result.stdout[:500]}")
        if result.returncode != 0:
            logger.warning(f"Claude exit code: {result.returncode}, stderr: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        logger.warning("Claude timed out after 180s")
    except Exception as e:
        logger.error(f"Claude trigger failed: {e}")

def watch_needs_action():
    """Watch Needs_Action folder and trigger Claude when files appear."""
    needs_action = VAULT_PATH / "Needs_Action"
    known_files = set(needs_action.glob("*.md"))
    logger.info(f"Watching {needs_action} for new files...")
    while True:
        time.sleep(10)
        current_files = set(needs_action.glob("*.md"))
        new_files = current_files - known_files
        if new_files:
            logger.info(f"New files detected: {[f.name for f in new_files]}")
            trigger_claude(
                "Check the /Needs_Action folder. For each new .md file, "
                "read its type and skill fields, execute the relevant Agent Skill "
                "from /Agent_Skills/, create a Plan.md in /Plans/, and if action "
                "is needed write an approval file to /Pending_Approval/. "
                "Update Dashboard.md when done."
            )
            known_files = current_files

def watch_pending_approval():
    """Watch Pending_Approval folder and log when files appear."""
    pending = VAULT_PATH / "Pending_Approval"
    pending.mkdir(parents=True, exist_ok=True)
    known_files = set(pending.glob("*.md"))
    logger.info(f"Watching {pending} for pending approval files... (found {len(known_files)} existing)")
    while True:
        try:
            time.sleep(10)
            current_files = set(pending.glob("*.md"))
            new_files = current_files - known_files
            if new_files:
                logger.info(f"⏳ Pending approval files: {[f.name for f in new_files]}")
                logger.info("   → Move to /Approved to execute, or /Rejected to discard")
            known_files = current_files
        except Exception as e:
            logger.error(f"watch_pending_approval error: {e}")

def watch_approved():
    """Watch Approved folder and trigger Claude or LinkedIn poster."""
    approved = VAULT_PATH / "Approved"
    approved.mkdir(parents=True, exist_ok=True)
    known_files = set(approved.glob("*.md"))
    logger.info(f"Watching {approved} for approved files... (found {len(known_files)} existing)")

    while True:
        try:
            time.sleep(5)
            current_files = set(approved.glob("*.md"))
            new_files = current_files - known_files

            if new_files:
                logger.info(f"New approved files: {[f.name for f in new_files]}")
                for f in new_files:
                    logger.info(f"✅ Approved file detected: {f.name}")

                    if f.name.startswith("LINKEDIN"):
                        # Run the LinkedIn poster script
                        logger.info("Triggering LinkedIn poster...")
                        subprocess.run(
                            ["python",
                             str(SCRIPTS_DIR / "linkedin_poster.py")],
                            check=False
                        )

                    elif f.name.startswith("EMAIL") or f.name.startswith("TEST_EMAIL"):
                        # Trigger Claude to send via email MCP
                        logger.info("Triggering Claude for email sending...")
                        trigger_claude(
                            "An email has been approved in /Approved. "
                            "Send it using the email MCP server. "
                            "Log the result to /Logs and move the file to /Done."
                        )

                    else:
                        # Generic approved file — trigger Claude
                        logger.info(f"Triggering Claude for approved: {f.name}")
                        trigger_claude(
                            f"File {f.name} has been approved in /Approved. "
                            "Execute the approved action and log results to /Logs."
                        )

                known_files = current_files
        except Exception as e:
            logger.error(f"watch_approved error: {e}")


def main():
    acquire_lock()

    logger.info("=" * 50)
    logger.info("AI Employee Orchestrator Starting")
    logger.info(f"Vault: {VAULT_PATH}")
    logger.info(f"DRY_RUN: {DRY_RUN}")
    logger.info("=" * 50)

    # Start watcher threads (all 4 watchers)
    run_script_in_thread("gmail_watcher.py")
    run_script_in_thread("filesystem_watcher.py")
    run_script_in_thread("whatsapp_watcher.py")
    run_script_in_thread("linkedin_watcher.py")

    # Watch for file changes (main threads)
    t_na = threading.Thread(target=watch_needs_action, daemon=True, name="watch_needs_action")
    t_pa = threading.Thread(target=watch_pending_approval, daemon=True, name="watch_pending_approval")
    t_ap = threading.Thread(target=watch_approved, daemon=True, name="watch_approved")
    t_na.start()
    t_pa.start()
    t_ap.start()

    logger.info("All watchers running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(60)
            logger.info("Orchestrator heartbeat — all systems running")
    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user.")

if __name__ == "__main__":
    main()
