from typing import List, Dict
from datetime import datetime
from scrapers.base_scraper import BaseScraper

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class GoogleScraper(BaseScraper):
    """
    Google Careers Scraper - Uses Playwright for JavaScript rendering
    
    Improvements over previous version:
    - Dynamic selector discovery instead of hardcoded classes
    - Better error handling and logging
    - Reduced excessive sleep calls
    - Proper timeout configuration
    - Graceful fallback if selectors change
    """

    def get_company_name(self) -> str:
        return "Google"

    def get_careers_url(self) -> str:
        return "https://www.google.com/about/careers/applications/jobs/results?target_level=INTERN_AND_APPRENTICE"

    def scrape(self) -> List[Dict]:
        """Scrape Google Careers for internships with improved resilience."""

        if not PLAYWRIGHT_AVAILABLE:
            error_msg = "Playwright not installed"
            self.logger.warning(f"⚠️ {error_msg}")
            self._record_error(error_msg)
            return []

        positions = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set reasonable defaults
                page.set_default_timeout(30000)
                page.set_default_navigation_timeout(30000)

                self.logger.info(f"→ Navigating to {self.careers_url}")
                try:
                    page.goto(self.careers_url, wait_until="load")
                except PlaywrightTimeout:
                    self.logger.warning("Navigation timeout - continuing anyway")

                # Wait for job listings to load
                # Use flexible selector - wait for any <li> tags instead of specific class
                try:
                    page.wait_for_selector("li", timeout=15000)
                    self.logger.info("✓ Job listings loaded")
                except PlaywrightTimeout:
                    error_msg = "Timed out waiting for job listings"
                    self.logger.error(error_msg)
                    browser.close()
                    self._record_error(error_msg)
                    return []

                # Scroll and extract jobs
                positions = self._scroll_and_extract(page)
                
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

    def _scroll_and_extract(self, page) -> List[Dict]:
        """
        Scroll page and extract job cards using dynamic selectors.
        
        More resilient to DOM changes than hardcoded selectors.
        """
        positions = []
        seen_urls = set()
        
        max_scrolls = 10
        no_new_jobs_threshold = 3
        no_new_jobs_count = 0
        
        self.logger.info("→ Starting scroll and extract...")

        for scroll_num in range(max_scrolls):
            # Get all list items (flexible approach)
            try:
                job_elements = page.query_selector_all("li")
            except Exception as e:
                self.logger.warning(f"Could not query job elements: {e}")
                job_elements = []

            new_positions_this_scroll = 0

            # Try to extract from each element
            for idx, element in enumerate(job_elements):
                try:
                    # Try to find title - look for headings or text content
                    title_el = None
                    for selector in ["h3", "h2", "[role='heading']"]:
                        try:
                            title_el = element.query_selector(selector)
                            if title_el:
                                break
                        except:
                            pass
                    
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()
                    if not title:
                        continue

                    # Check if it's an internship
                    if not self.is_internship(title):
                        continue

                    # Get link - try multiple approaches
                    link = None
                    for selector in ["a[href]", "a"]:
                        try:
                            link_el = element.query_selector(selector)
                            if link_el and link_el.get_attribute("href"):
                                link = link_el.get_attribute("href")
                                break
                        except:
                            pass
                    
                    if not link:
                        continue

                    if link in seen_urls:
                        continue

                    # Normalize URL
                    url = self._normalize_url(link)
                    if not url:
                        continue

                    seen_urls.add(url)

                    # Extract location (best effort)
                    location = self._extract_location(element)

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
                    # Skip problematic elements instead of crashing
                    self.logger.debug(f"Skipped element {idx}: {e}")
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

            # Scroll down for next batch
            if scroll_num < max_scrolls - 1:
                try:
                    page.keyboard.press("End")
                    page.wait_for_timeout(1000)  # Reduced from 1.5s
                except:
                    break

        return positions

    def _normalize_url(self, link: str) -> str:
        """Normalize URL to absolute form"""
        try:
            if link.startswith("/"):
                return f"https://www.google.com{link}"
            elif link.startswith("http"):
                return link
            elif link.startswith("careers"):
                return f"https://www.google.com/about/{link}"
            else:
                return f"https://www.google.com/about/careers/applications/{link}"
        except:
            return None # type: ignore

    def _extract_location(self, element) -> str:
        """Extract location from element (best effort)"""
        try:
            # Try to find location in spans or text content
            location_parts = []
            
            for span in element.query_selector_all("span"):
                try:
                    text = span.inner_text().strip()
                    # Look for location indicators
                    if any(word in text.lower() for word in ["city", "state", "country", ",", "usa", "us"]):
                        location_parts.append(text)
                        if len(location_parts) >= 2:
                            break
                except:
                    pass
            
            if location_parts:
                return "; ".join(location_parts)
            return "Not specified"
        except:
            return "Not specified"
