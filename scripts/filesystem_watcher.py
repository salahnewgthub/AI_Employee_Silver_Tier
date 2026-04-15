import sys
import os
from pathlib import Path
from datetime import datetime
import shutil

sys.path.insert(0, str(Path(__file__).parent))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

VAULT_PATH = os.getenv("VAULT_PATH", r"E:\AI_Employee_Silver_Tier\Vault")
INBOX_PATH = Path(VAULT_PATH) / "Inbox"
NEEDS_ACTION_PATH = Path(VAULT_PATH) / "Needs_Action"

class DropFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        # Ignore markdown files (they're created by Claude)
        if source.suffix == ".md":
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = NEEDS_ACTION_PATH / f"FILE_{timestamp}_{source.name}"
        try:
            shutil.copy2(source, dest)
            # Create a metadata .md companion file
            meta = NEEDS_ACTION_PATH / f"FILE_{timestamp}_{source.stem}.md"
            meta.write_text(f"""---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size} bytes
received: {datetime.now().isoformat()}
status: pending
---

A new file was dropped into the Inbox folder.
Please review and take appropriate action.
""", encoding="utf-8")
            print(f"File detected and moved to Needs_Action: {source.name}")
        except Exception as e:
            print(f"Error handling file drop: {e}")

if __name__ == "__main__":
    INBOX_PATH.mkdir(parents=True, exist_ok=True)
    NEEDS_ACTION_PATH.mkdir(parents=True, exist_ok=True)
    handler = DropFolderHandler()
    observer = Observer()
    observer.schedule(handler, str(INBOX_PATH), recursive=False)
    observer.start()
    print(f"Filesystem watcher running. Drop files into: {INBOX_PATH}")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()