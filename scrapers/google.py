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
        # Updated URL with correct filter for internships
        return "https://www.google.com/about/careers/applications/jobs/results?target_level=INTERN_AND_APPRENTICE"

    def scrape(self) -> List[Dict]:
        """Scrape Google Careers for internships."""

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

                # Wait for job cards to load
                try:
                    page.wait_for_selector("li.lLd3Je", timeout=15000)
                    time.sleep(2)  # Extra wait for dynamic content
                except PlaywrightTimeout:
                    print("  ⚠️ Timed out waiting for job cards.")
                    browser.close()
                    return []

                # -------------------------------
                #       AUTO-SCROLL TO LOAD JOBS
                # -------------------------------
                print("  → Scrolling to load jobs...")

                last_count = 0
                for scroll_attempt in range(20):  # up to 20 scroll cycles
                    page.mouse.wheel(0, 5000)
                    time.sleep(1.5)

                    current_count = page.locator("li.lLd3Je").count()
                    
                    if current_count == last_count and scroll_attempt > 3:
                        break
                    last_count = current_count

                print(f"  → Loaded {last_count} job cards.")

                # -------------------------------
                #      PARSE EACH JOB CARD
                # -------------------------------
                
                job_cards = page.locator("li.lLd3Je").all()
                print(f"  → Found {len(job_cards)} job listings to parse.")

                for i, card in enumerate(job_cards):
                    try:
                        # Extract title from h3.QJPWVe
                        title = card.locator("h3.QJPWVe").inner_text(timeout=2000).strip()

                        # Internship filter
                        if not self.is_internship(title):
                            continue

                        # Extract location from span.pwO9Dc
                        location = "Not specified"
                        try:
                            # Get all location spans
                            location_container = card.locator("span.pwO9Dc").first
                            location_parts = location_container.locator("span.r0wTof").all()
                            
                            if location_parts:
                                locations = [loc.inner_text(timeout=1000).strip() for loc in location_parts]
                                # Check if there are more locations
                                more_indicator = location_container.locator("span.BVHzed, span.Z2gFhf").count()
                                if more_indicator > 0:
                                    location = f"{'; '.join(locations[:2])}; +"
                                else:
                                    location = "; ".join(locations)
                            else:
                                # Fallback to getting all text
                                location = location_container.inner_text(timeout=1000).strip()
                        except:
                            pass

                        # Extract URL from the anchor tag with class WpHeLc
                        link = ""
                        try:
                            link = card.locator("a.WpHeLc").get_attribute("href", timeout=2000)
                        except:
                            continue

                        if not link:
                            continue

                        # Handle relative URLs
                        if link.startswith("/"):
                            url = f"https://www.google.com{link}"
                        elif not link.startswith("http"):
                            url = f"https://www.google.com/about/careers/applications/{link}"
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

                        print(f"  ✓ Found: {title[:50]}...")

                    except Exception as e:
                        print(f"  ⚠️ Error parsing card {i}: {e}")
                        continue

                browser.close()
                print(f"  ✓ Extracted {len(positions)} internship positions.")

        except Exception as e:
            print(f"  ✗ Error scraping {self.company_name}: {e}")

        return positions