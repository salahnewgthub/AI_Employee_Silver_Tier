import sys
import os
from pathlib import Path

# Fix import path
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher
from datetime import datetime

VAULT_PATH = os.getenv("VAULT_PATH", r"E:\AI_Employee_Silver_Tier\Vault")
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "")

# OAuth scopes — must match what was used when token was first created
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailWatcher(BaseWatcher):
    def __init__(self):
        super().__init__(vault_path=VAULT_PATH, check_interval=120)
        self.processed_ids = self._load_processed_ids()
        self._setup_gmail()

    def _load_processed_ids(self) -> set:
        """Load processed email IDs from disk so they survive restarts."""
        state_file = Path(__file__).parent.parent / "gmail_state.json"
        try:
            import json
            if state_file.exists():
                data = json.loads(state_file.read_text())
                self.logger.info(f"Loaded {len(data.get('processed_ids', []))} processed email IDs from disk.")
                return set(data.get("processed_ids", []))
        except Exception as e:
            self.logger.warning(f"Could not load gmail_state.json: {e}")
        return set()

    def _save_processed_ids(self):
        """Persist processed email IDs to disk."""
        state_file = Path(__file__).parent.parent / "gmail_state.json"
        try:
            import json
            # Only keep the last 500 IDs to prevent file growing forever
            ids_list = list(self.processed_ids)[-500:]
            state_file.write_text(json.dumps({"processed_ids": ids_list}), encoding="utf-8")
        except Exception as e:
            self.logger.warning(f"Could not save gmail_state.json: {e}")

    def _setup_gmail(self):
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None
            token_path = Path(CREDENTIALS_PATH)

            # ── Load existing token ──────────────────────────────────────────
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

                # ── Refresh silently if expired ──────────────────────────────────
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Token expired — refreshing silently...")
                    creds.refresh(Request())
                    self.logger.info("Token refreshed successfully.")
                    # Save the refreshed token back to disk
                    token_path.write_text(creds.to_json(), encoding="utf-8")

            # ── No valid token — trigger browser re-auth ─────────────────────
            if not creds or not creds.valid:
                self.logger.info("No valid token found — launching browser for re-authentication...")

                # Look for client_secrets.json next to the token file
                secrets_path = token_path.parent / "client_secrets.json"
                if not secrets_path.exists():
                    # Fallback: look in the scripts folder
                    secrets_path = Path(__file__).parent / "client_secrets.json"

                if not secrets_path.exists():
                    raise FileNotFoundError(
                        f"client_secrets.json not found at {secrets_path}. "
                        "Download it from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
                creds = flow.run_local_server(port=0)

                # Save the new token for future runs
                token_path.write_text(creds.to_json(), encoding="utf-8")
                self.logger.info(f"New token saved to {token_path}")

            self.service = build("gmail", "v1", credentials=creds)
            self.logger.info("Gmail API connected successfully")

        except Exception as e:
            self.logger.error(f"Gmail setup failed: {e}")
            self.service = None

    def check_for_updates(self) -> list:
        if not self.service:
            return []
        try:
            # Use 'newer_than:1d' to only check emails from the last 24 hours
            # This avoids flooding you with action files for 1000+ old unread emails
            results = self.service.users().messages().list(
                userId="me", q="is:unread newer_than:1d"
            ).execute()
            messages = results.get("messages", [])

            # Filter out already-processed emails
            new_messages = [m for m in messages if m["id"] not in self.processed_ids]

            if new_messages:
                self.logger.info(
                    f"Found {len(new_messages)} new unread email(s) "
                    f"(out of {len(messages)} total unread in last 24h)"
                )

            return new_messages
        except Exception as e:
            self.logger.error(f"Gmail fetch error: {e}")
            return []

    def create_action_file(self, message) -> Path:
        msg = self.service.users().messages().get(
            userId="me", id=message["id"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        email_from = headers.get("From", "Unknown")
        subject = headers.get("Subject", "No Subject")
        snippet = msg.get("snippet", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        content = f"""---
type: email
from: {email_from}
subject: {subject}
received: {datetime.now().isoformat()}
priority: high
status: pending
skill: process_email_skill
---

## Email Content
{snippet}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
        filepath = self.needs_action / f"EMAIL_{timestamp}_{message['id'][:8]}.md"
        filepath.write_text(content, encoding="utf-8")
        self.processed_ids.add(message["id"])
        self._save_processed_ids()  # Persist to disk
        return filepath


if __name__ == "__main__":
    watcher = GmailWatcher()
    watcher.run()
