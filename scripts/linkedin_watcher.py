import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent))

VAULT_PATH = os.getenv("VAULT_PATH", r"E:\AI_Employee_Silver_Tier\Vault")

# LinkedIn watcher — generates scheduled post drafts
# (Silver Tier: posts via MCP after human approval)

STATE_FILE = Path(VAULT_PATH).parent / "linkedin_state.json"

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_post_draft": None}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def should_create_post_draft():
    state = load_state()
    if not state["last_post_draft"]:
        return True
    last = datetime.fromisoformat(state["last_post_draft"])
    return datetime.now() - last > timedelta(days=2)

def create_linkedin_draft():
    needs_action = Path(VAULT_PATH) / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    content = f"""---
type: linkedin_draft_request
created: {datetime.now().isoformat()}
status: pending
skill: linkedin_post_skill
---

## LinkedIn Post Request

Claude should read Business_Goals.md and Company_Handbook.md,
then draft a professional LinkedIn post to generate business leads.

The draft must be saved to /Pending_Approval for human review.
Do NOT post directly.
"""
    filepath = needs_action / f"LINKEDIN_draft_request_{timestamp}.md"
    filepath.write_text(content, encoding="utf-8")
    state = load_state()
    state["last_post_draft"] = datetime.now().isoformat()
    save_state(state)
    print(f"LinkedIn draft request created: {filepath}")

if __name__ == "__main__":
    if should_create_post_draft():
        create_linkedin_draft()
    else:
        print("LinkedIn: no new draft needed yet")