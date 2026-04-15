import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

SESSION_PATH = Path(os.getenv("LINKEDIN_SESSION_PATH",
                              r"E:\AI_Employee_Silver_Tier\linkedin_session"))

def login():
    SESSION_PATH.mkdir(parents=True, exist_ok=True)
    print(f"\nLinkedIn session will be saved to: {SESSION_PATH}")
    print("\nINSTRUCTIONS:")
    print("  1. A browser window will open")
    print("  2. Enter your LinkedIn email and password")
    print("  3. If LinkedIn asks for a PIN — check your email and enter it")
    print("  4. Wait until your LinkedIn FEED is fully loaded")
    print("  5. Come back here and press Enter\n")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(SESSION_PATH),
            headless=False,
            slow_mo=100,
            args=["--start-maximized"]
        )

        page = browser.new_page() if not browser.pages else browser.pages[0]

        # Go to login page
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        print("Browser opened. Please log in now...")

        # Wait for YOU to finish everything (login + PIN + feed loaded)
        input("\n   >>> Press Enter ONLY after your LinkedIn feed is fully visible: ")

        # Check what page we ended up on
        current_url = page.url
        print(f"\nCurrent URL: {current_url}")

        if "feed" in current_url or "mynetwork" in current_url or "linkedin.com/in/" in current_url:
            print("\n✅ LinkedIn login successful! Session saved.")
            print(f"   Session stored at: {SESSION_PATH}")
        elif "checkpoint" in current_url or "challenge" in current_url:
            print("\n⚠️  LinkedIn is still showing a verification page.")
            print("   Please complete the verification in the browser, then run this script again.")
        elif "login" in current_url or "signup" in current_url:
            print("\n❌ Still on login page. Please complete login and run again.")
        else:
            print(f"\n✅ Session likely saved. URL: {current_url}")
            print("   If posting fails later, run this login script again.")

        # Keep browser open a moment so session fully saves to disk
        print("\nSaving session to disk...")
        time.sleep(3)
        browser.close()
        print("Done. Browser closed.")

if __name__ == "__main__":
    login()