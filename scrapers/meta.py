from datetime import datetime
from typing import Dict, List

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from scrapers.base_scraper import BaseScraper


class MetaScraper(BaseScraper):
    """
    Meta Careers Scraper - Uses Playwright for JavaScript rendering
    
    IMPORTANT:
    - Meta actively blocks scrapers and has explicit ToS against scraping
    - This implementation uses browser automation which is more reliable than API
    - May still be blocked by Meta's anti-bot measures
    - Consider using LinkedIn API instead (Meta owns LinkedIn)
    
    Improvements:
    - Uses Playwright instead of broken GraphQL endpoint
    - Better error handling and logging
    - Graceful degradation when selectors change
    - Respects rate limiting
    """
    
    def get_company_name(self) -> str:
        return "Meta"
    
    def get_careers_url(self) -> str:
        return "https://www.metacareers.com/jobs/search/"
    
    def scrape(self) -> List[Dict]:
        """Scrape Meta Careers using browser automation."""
        
        if not PLAYWRIGHT_AVAILABLE:
            error_msg = "Playwright not installed"
            self.logger.warning(f"⚠️ {error_msg}")
            self._record_error(error_msg)
            return []

        positions = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                page.set_default_timeout(30000)
                page.set_default_navigation_timeout(30000)

                url = f"{self.get_careers_url()}?q=internship"
                self.logger.info(f"→ Navigating to {url}")

                try:
                    page.goto(url, wait_until="load")
                except PlaywrightTimeout:
                    self.logger.warning("Navigation timeout - page may still load")

                # Wait for job listings to appear
                try:
                    page.wait_for_selector("li, div[role='option'], [data-testid*='job']", timeout=15000)
                    self.logger.info("✓ Job listings loaded")
                except PlaywrightTimeout:
                    error_msg = "No job listings found - Meta may have changed structure or blocked request"
                    self.logger.warning(error_msg)
                    browser.close()
                    self._record_error(error_msg)
                    return []

                # Scroll and extract jobs
                positions = self._scroll_and_extract_meta(page)

                browser.close()
                
                # Record success
                if positions:
                    self._record_success(len(positions))
                    self.logger.info(f"✓ Extracted {len(positions)} internship positions")
                else:
                    self.logger.warning("No positions found")

        except Exception as e:
            error_msg = f"Error scraping {self.company_name}: {str(e)}"
            self.logger.exception(error_msg)
            self._record_error(error_msg)

        return positions

    def _scroll_and_extract_meta(self, page) -> List[Dict]:
        """Extract job listings from Meta Careers page."""
        positions = []
        seen_urls = set()

        max_scrolls = 8
        no_new_jobs_threshold = 2
        no_new_jobs_count = 0
        
        self.logger.info("→ Starting scroll and extract...")

        for scroll_num in range(max_scrolls):
            # Get all potential job cards
            try:
                job_cards = page.query_selector_all("li, div[role='option']")
            except Exception as e:
                self.logger.warning(f"Could not query job cards: {e}")
                job_cards = []

            new_positions_this_scroll = 0

            for idx, card in enumerate(job_cards):
                try:
                    # Try to extract title with multiple selectors
                    title_el = None
                    for selector in ["h3", "h2", "[role='heading']", "span"]:
                        try:
                            els = card.query_selector_all(selector)
                            if els:
                                title_el = els[0]
                                break
                        except:
                            pass
                    
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()
                    if not title or len(title) < 3:
                        continue

                    # Check if internship
                    if not self.is_internship(title):
                        continue

                    # Extract URL
                    url = None
                    try:
                        link_el = card.query_selector("a[href]")
                        if link_el:
                            url = link_el.get_attribute("href")
                    except:
                        pass

                    # Normalize URL
                    if not url.startswith("http"):
                        url = f"https://www.metacareers.com{url}"

                    if url in seen_urls:
                        continue

                    seen_urls.add(url)

                    # Extract location
                    location = "Not specified"
                    try:
                        for el in card.query_selector_all("span, div"):
                            text = el.inner_text().strip()
                            # Look for location-like strings
                            if any(word in text.lower() for word in [",", "city", "state", "usa", "remote"]):
                                if len(text) < 100:  # Reasonable length for location
                                    location = text
                                    break
                    except:
                        pass

                    positions.append({
                        "title": title,
                        "location": location,
                        "url": url,
                        "posted_date": datetime.now(),
                        "description": "",
                        "requirements": []
                    })

                    new_positions_this_scroll += 1
                    self.logger.debug(f"✓ Found: {title[:50]}...")

                except Exception as e:
                    self.logger.debug(f"Skipped card {idx}: {e}")
                    continue

            # Check if we found new positions
            if new_positions_this_scroll == 0:
                no_new_jobs_count += 1
                if no_new_jobs_count >= no_new_jobs_threshold:
                    self.logger.info(f"No new positions in {no_new_jobs_threshold} scrolls - stopping")
                    break
            else:
                no_new_jobs_count = 0
                self.logger.info(f"  Scroll {scroll_num + 1}: Found {new_positions_this_scroll} new positions")

            # Scroll down
            if scroll_num < max_scrolls - 1:
                try:
                    page.keyboard.press("End")
                    page.wait_for_timeout(1500)
                except:
                    break

        return positions
