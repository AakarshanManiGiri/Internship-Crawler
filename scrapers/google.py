from typing import List, Dict
from datetime import datetime
from scrapers.base_scraper import BaseScraper
import time

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not installed. Install with: pip install playwright && playwright install chromium")


class GoogleScraper(BaseScraper):

    def get_company_name(self) -> str:
        return "Google"

    def get_careers_url(self) -> str:
        # Filter already set to internships only
        return "https://careers.google.com/jobs/results/?employment_type=INTERN"

    def scrape(self) -> List[Dict]:
        """Scrape Google Careers for internships (fully functional version)."""

        if not PLAYWRIGHT_AVAILABLE:
            print(f"  ⚠️ Playwright not available, skipping {self.company_name}")
            return []

        positions = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                print(f"  → Navigating to {self.careers_url}")
                page.goto(self.careers_url, timeout=45000)

                # Ensure job cards start loading
                try:
                    page.wait_for_selector("gc-card", timeout=15000)
                except PlaywrightTimeout:
                    print("  ⚠️ Timed out waiting for job cards.")
                    browser.close()
                    return []

                # -------------------------------
                #       AUTO-SCROLL TO LOAD JOBS
                # -------------------------------
                print("  → Scrolling to load jobs...")

                last_count = 0
                for _ in range(20):  # up to 20 scroll cycles
                    page.mouse.wheel(0, 5000)
                    time.sleep(1.2)

                    current_count = page.locator("gc-card").count()
                    if current_count == last_count:
                        break
                    last_count = current_count

                total_cards = page.locator("gc-card").count()
                print(f"  → Loaded {total_cards} job cards.")

                # -------------------------------
                #      PARSE EACH JOB CARD
                # -------------------------------
                for i in range(total_cards):
                    card = page.locator("gc-card").nth(i)

                    try:
                        # Extract title (shadow DOM safe via locator)
                        title = card.locator("h2").inner_text(timeout=2000).strip()

                        # Internship filter
                        if not self.is_internship(title):
                            continue

                        # Extract location
                        # Google uses a utility container with jsname="GZq3Ke"
                        location = (
                            card.locator("div[jsname='GZq3Ke']")
                            .inner_text(timeout=2000)
                            .strip()
                        )

                        # Extract URL (Google uses relative hrefs)
                        link = card.locator("a").get_attribute("href")
                        if not link:
                            continue

                        if link.startswith("/"):
                            url = f"https://careers.google.com{link}"
                        else:
                            url = link

                        positions.append({
                            "title": title,
                            "location": location,
                            "url": url,
                            "posted_date": datetime.now(),   # Google doesn't expose posted dates in list
                            "description": "",
                            "requirements": []
                        })

                    except Exception as e:
                        print(f"  ⚠️ Error parsing card {i}: {e}")
                        continue

                browser.close()
                print(f"  ✓ Extracted {len(positions)} internship positions.")

        except Exception as e:
            print(f"  ✗ Error scraping {self.company_name}: {e}")

        return positions
