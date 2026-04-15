import sys
import os
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

VAULT_PATH = os.getenv("VAULT_PATH", r"E:\AI_Employee_Silver_Tier\Vault")
SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH", r"E:\AI_Employee_Silver_Tier\whatsapp_session")
KEYWORDS = ["urgent", "asap", "invoice", "payment", "help", "deadline", "pricing"]


class WhatsAppWatcher(BaseWatcher):
    def __init__(self):
        super().__init__(vault_path=VAULT_PATH, check_interval=30)
        self.session_path = Path(SESSION_PATH)
        self.session_path.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self) -> list:
        try:
            from playwright.sync_api import sync_playwright
            messages = []

            with sync_playwright() as p:
                self.logger.info("Launching browser...")
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=False,
                    args=["--no-sandbox"],
                    slow_mo=500
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                self.logger.info("Navigating to WhatsApp Web...")
                page.goto("https://web.whatsapp.com", timeout=60000)

                self.logger.info("Waiting for WhatsApp to fully load...")

                # Wait for chat list container
                chat_loaded = False
                for selector in [
                    '#pane-side',
                    '[data-testid="chat-list"]',
                    'div[aria-label="Chat list"]'
                ]:
                    try:
                        page.wait_for_selector(selector, timeout=20000)
                        self.logger.info(f"Chat list found using selector: {selector}")
                        chat_loaded = True
                        break
                    except:
                        self.logger.info(f"Selector not found: {selector}, trying next...")

                if not chat_loaded:
                    screenshot_path = Path(VAULT_PATH).parent / "debug_screenshot.png"
                    page.screenshot(path=str(screenshot_path))
                    self.logger.warning(f"Could not load chats. Screenshot saved: {screenshot_path}")
                    browser.close()
                    return []

                # Wait for all chat rows to fully render
                self.logger.info("Waiting 5 seconds for full render...")
                time.sleep(5)

                # ── NEW APPROACH ──────────────────────────────────────────
                # Get ALL chat rows from the side panel, then for each row
                # check if it contains an unread badge and read its full text
                # ─────────────────────────────────────────────────────────

                # These are the actual conversation row containers
                chat_rows = page.query_selector_all(
                    '#pane-side [role="listitem"]'
                )
                self.logger.info(f"Total chat rows found: {len(chat_rows)}")

                if len(chat_rows) == 0:
                    # Fallback — try alternate container
                    chat_rows = page.query_selector_all(
                        '#pane-side div[tabindex="-1"]'
                    )
                    self.logger.info(f"Fallback rows found: {len(chat_rows)}")

                for i, row in enumerate(chat_rows):
                    try:
                        # Check if this row has an unread indicator inside it
                        unread_badge = row.query_selector(
                            'span[aria-label*="unread"], '
                            '[data-testid="icon-unread-count"], '
                            'span._ahlk, '       # WhatsApp internal class for unread dot
                            'div._ahlk'
                        )

                        if unread_badge is None:
                            continue  # skip read chats

                        # Read the full visible text of the whole chat row
                        # This gives: contact name + message preview + time
                        full_text = (row.inner_text() or "").strip()

                        # Log the real content now
                        self.logger.info(
                            f"[Row {i}] UNREAD chat content:\n{full_text[:200]}"
                        )

                        text_lower = full_text.lower()
                        matched = [kw for kw in KEYWORDS if kw in text_lower]

                        if matched:
                            self.logger.info(
                                f"[Row {i}] KEYWORD MATCH: {matched}"
                            )
                            messages.append({
                                "text": full_text,
                                "timestamp": datetime.now().isoformat(),
                                "keywords_found": matched
                            })
                        else:
                            self.logger.info(
                                f"[Row {i}] No keyword match — skipping."
                            )

                    except Exception as e:
                        self.logger.warning(f"[Row {i}] Could not read: {e}")

                if not messages:
                    self.logger.info(
                        "No keyword matches in any unread chat. All clear."
                    )

                browser.close()

            return messages

        except Exception as e:
            self.logger.error(f"WhatsApp watcher error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def create_action_file(self, message) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keywords = ", ".join(message.get("keywords_found", []))
        content = f"""---
type: whatsapp
received: {message['timestamp']}
keywords_matched: {keywords}
priority: high
status: pending
skill: process_whatsapp_skill
---

## Message Content
{message['text']}

## Suggested Actions
- [ ] Draft reply
- [ ] Escalate if urgent
"""
        filepath = self.needs_action / f"WHATSAPP_{timestamp}.md"
        filepath.write_text(content, encoding="utf-8")
        return filepath


if __name__ == "__main__":
    watcher = WhatsAppWatcher()
    watcher.run()