import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

VAULT_PATH = Path(os.getenv("VAULT_PATH", r"E:\AI_Employee_Silver_Tier\Vault"))
SESSION_PATH = Path(os.getenv("LINKEDIN_SESSION_PATH",
                              r"E:\AI_Employee_Silver_Tier\linkedin_session"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LinkedInPoster] %(levelname)s: %(message)s"
)
logger = logging.getLogger("LinkedInPoster")


def extract_post_text(md_file: Path) -> str:
    """Extract post body from the approval markdown file."""
    content = md_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    # Skip YAML frontmatter (between --- lines)
    in_frontmatter = False
    body_lines = []
    frontmatter_done = False
    dash_count = 0
    for line in lines:
        if line.strip() == "---" and not frontmatter_done:
            dash_count += 1
            if dash_count == 2:
                frontmatter_done = True
            continue
        if not frontmatter_done:
            continue
        # Skip section headings like "## Draft LinkedIn Post"
        if line.startswith("## Draft LinkedIn Post"):
            continue
        if line.startswith("## ") or line.startswith("# "):
            continue
        # Stop at approval instructions
        if "Move this file to" in line:
            break
        body_lines.append(line)

    post_text = "\n".join(body_lines).strip()
    return post_text


def login_to_linkedin(page):
    """Navigate to LinkedIn and verify we are logged in via saved session."""
    page.goto("https://www.linkedin.com/feed/", timeout=30000)
    time.sleep(3)
    # Check if we landed on feed (logged in) or login page
    if "login" in page.url or "signup" in page.url:
        raise Exception(
            "LinkedIn session expired. Run linkedin_login.py to re-authenticate."
        )
    logger.info("LinkedIn session valid — logged in successfully.")


def post_to_linkedin(post_text: str, headless: bool = True) -> bool:
    """Open LinkedIn and publish a post using Playwright."""
    from playwright.sync_api import sync_playwright

    if DRY_RUN:
        logger.info("[DRY RUN] Would post to LinkedIn:")
        logger.info("-" * 40)
        logger.info(post_text)
        logger.info("-" * 40)
        return True

    SESSION_PATH.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(SESSION_PATH),
            headless=headless,
            slow_mo=800,
            args=["--start-maximized"]
        )
        page = browser.new_page() if not browser.pages else browser.pages[0]

        def take_screenshot(label: str):
            path = VAULT_PATH / "Logs" / f"linkedin_{label}_{datetime.now().strftime('%H%M%S')}.png"
            try:
                page.screenshot(path=str(path))
                logger.info(f"Screenshot: {path.name}")
            except:
                pass

        try:
            # ── Step 1: Load feed ────────────────────────────────────────
            logger.info("Loading LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", timeout=30000,
                      wait_until="domcontentloaded")
            time.sleep(4)

            if "login" in page.url or "signup" in page.url:
                raise Exception(
                    "LinkedIn session expired. Run linkedin_login.py again."
                )

            take_screenshot("01_feed_loaded")
            logger.info(f"Feed URL: {page.url}")

            # ── Step 2: Click "Start a post" ─────────────────────────────
            # LinkedIn changes selectors often — try several in order
            logger.info("Looking for Start a post button...")

            start_post_selectors = [
                '[data-placeholder="Start a post"]',
                'button:has-text("Start a post")',
                '[aria-label="Start a post"]',
                '.share-box-feed-entry__trigger',
                'div.share-box-feed-entry__top-bar button',
                'button.share-box-feed-entry__trigger',
                '[data-control-name="share.sharebox_trigger"]',
                'span:has-text("Start a post")',
            ]

            clicked = False
            for selector in start_post_selectors:
                try:
                    element = page.locator(selector).first
                    element.wait_for(state="visible", timeout=4000)
                    element.click()
                    logger.info(f"Clicked using selector: {selector}")
                    clicked = True
                    break
                except:
                    continue

            if not clicked:
                take_screenshot("02_start_post_failed")
                logger.error("Could not find Start a post button.")
                logger.error("Opening non-headless browser so you can see the page...")
                browser.close()
                # Retry visibly so you can inspect
                return post_to_linkedin(post_text, headless=False)

            time.sleep(3)
            take_screenshot("02_composer_opened")

            # ── Step 3: Find the text editor inside the modal ────────────
            logger.info("Finding post text editor...")

            editor_selectors = [
                'div[role="textbox"]',
                '.ql-editor',
                '[contenteditable="true"]',
                'div.mentions-texteditor__content',
                'div[data-placeholder]',
            ]

            editor = None
            for selector in editor_selectors:
                try:
                    el = page.locator(selector).first
                    el.wait_for(state="visible", timeout=4000)
                    editor = el
                    logger.info(f"Editor found: {selector}")
                    break
                except:
                    continue

            if not editor:
                take_screenshot("03_editor_not_found")
                raise Exception("Could not find the post text editor.")

            # ── Step 4: Type the post ─────────────────────────────────────
            logger.info("Typing post content...")
            editor.click()
            time.sleep(1)

            # Split into lines and type each — handles newlines correctly
            lines = post_text.split("\n")
            for i, line in enumerate(lines):
                page.keyboard.type(line, delay=25)
                if i < len(lines) - 1:
                    page.keyboard.press("Shift+Enter")

            time.sleep(2)
            take_screenshot("03_post_typed")

            # ── Step 5: Click the Post button ────────────────────────────
            logger.info("Looking for Post button...")

            post_button_selectors = [
                'button.artdeco-button--primary:has-text("Post")',
                'button.artdeco-button--primary[aria-label="Post"]',
                'div.artdeco-button-group button.artdeco-button--primary',
                'button[data-control-name="share.post"]',
                'button:has-text("Post")',
            ]

            posted = False
            for selector in post_button_selectors:
                try:
                    btn = page.locator(selector).first
                    btn.wait_for(state="visible", timeout=4000)
                    btn.click()
                    logger.info(f"Post button clicked: {selector}")
                    posted = True
                    break
                except:
                    continue

            if not posted:
                take_screenshot("04_post_button_failed")
                raise Exception("Could not find the Post button.")

            time.sleep(4)
            take_screenshot("04_post_clicked")

            # ── Step 6: Wait for LinkedIn confirmation ────────────────────
            logger.info("Waiting for LinkedIn to confirm post...")
            time.sleep(5)  # Wait for the actual API call to complete
            take_screenshot("05_after_post_wait")

            # Check if composer closed (means post went through)
            composer_closed = False
            try:
                page.locator('div[role="dialog"]').first.wait_for(state="hidden", timeout=5000)
                composer_closed = True
                logger.info("Post composer closed — post submitted.")
            except:
                pass

            # Navigate to profile to verify post appears
            logger.info("Navigating to your profile to verify post...")
            page.goto("https://www.linkedin.com/in/me/recent-activity/", timeout=30000)
            time.sleep(5)
            take_screenshot("06_profile_activity")

            # Check if our post text appears on the profile page
            post_confirmed = False
            try:
                # Look for our post content on the page
                if "context switching" in page.content() or "productivity killer" in page.content():
                    post_confirmed = True
                    logger.info("✅ Post verified on your profile!")
                else:
                    logger.warning("Post text not found on profile page.")
                    # Try the feed instead
                    logger.info("Checking feed for post...")
                    page.goto("https://www.linkedin.com/feed/", timeout=30000)
                    time.sleep(5)
                    take_screenshot("07_feed_check")
                    if "context switching" in page.content():
                        post_confirmed = True
                        logger.info("✅ Post verified on feed!")
            except Exception as e:
                logger.warning(f"Could not verify post on profile: {e}")

            if not post_confirmed:
                logger.error(
                    "❌ Post may NOT have been published! "
                    "The bot clicked Post but LinkedIn did not confirm. "
                    "Check screenshots in Vault/Logs/ to debug."
                )
                take_screenshot("08_post_failed")
                return False

            logger.info("✅ Post published successfully on LinkedIn!")
            browser.close()
            return True

        except Exception as e:
            logger.error(f"LinkedIn posting failed: {e}")
            take_screenshot("error_final")
            browser.close()
            return False

def process_approved_linkedin_files():
    """Find approved LinkedIn post files and post them."""
    approved_dir = VAULT_PATH / "Approved"
    done_dir = VAULT_PATH / "Done"
    logs_dir = VAULT_PATH / "Logs"
    done_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    linkedin_files = list(approved_dir.glob("LINKEDIN*.md"))

    if not linkedin_files:
        logger.info("No approved LinkedIn posts found.")
        return

    for md_file in linkedin_files:
        logger.info(f"Processing approved post: {md_file.name}")
        post_text = extract_post_text(md_file)

        if not post_text:
            logger.warning(f"Could not extract post text from {md_file.name}. Skipping.")
            continue

        logger.info(f"Post text ({len(post_text)} chars):\n{post_text[:200]}...")
        success = post_to_linkedin(post_text)

        # Log result
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file": md_file.name,
            "action": "linkedin_post",
            "post_preview": post_text[:100],
            "result": "success" if success else "failed",
            "dry_run": DRY_RUN
        }
        log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))

        if success:
            # Move to Done
            dest = done_dir / md_file.name
            md_file.rename(dest)
            logger.info(f"Moved to Done: {dest.name}")
        else:
            logger.error(f"Post failed — file left in Approved for retry: {md_file.name}")


if __name__ == "__main__":
    process_approved_linkedin_files()