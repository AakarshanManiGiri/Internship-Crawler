from typing import List, Dict
from datetime import datetime
from scrapers.base_scraper import BaseScraper
import json
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
        # URL with filter for internships
        return "https://careers.google.com/jobs/results/?employment_type=INTERN"
    
    def scrape(self) -> List[Dict]:
        """Scrape Google Careers using Playwright"""
        
        if not PLAYWRIGHT_AVAILABLE:
            print(f"  ⚠️  Playwright not available, skipping {self.company_name}")
            return []
        
        positions = []
        
        try:
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                print(f"  → Navigating to {self.careers_url}")
                page.goto(self.careers_url, timeout=30000)
                
                # Wait for jobs to load (Google uses dynamic loading)
                try:
                    page.wait_for_selector('[role="listitem"]', timeout=10000)
                    time.sleep(2)  # Extra wait for JavaScript
                except PlaywrightTimeout:
                    print(f"  ⚠️  No jobs found or timeout")
                    browser.close()
                    return []
                
                # Get all job listings
                job_cards = page.query_selector_all('[role="listitem"]')
                print(f"  → Found {len(job_cards)} job listings")
                
                for card in job_cards[:10]:  # Limit to first 10 for testing
                    try:
                        # Extract job details
                        title_elem = card.query_selector('[class*="title"]') or card.query_selector('h3')
                        location_elem = card.query_selector('[class*="location"]')
                        link_elem = card.query_selector('a[href*="/jobs/results/"]')
                        
                        if not title_elem or not link_elem:
                            continue
                        
                        title = title_elem.inner_text().strip()
                        
                        # Only process internships
                        if not self.is_internship(title):
                            continue
                        
                        location = location_elem.inner_text().strip() if location_elem else "Multiple locations"
                        
                        # Build full URL
                        href = link_elem.get_attribute('href')
                        if href.startswith('/'):
                            url = f"https://careers.google.com{href}"
                        else:
                            url = href
                        
                        positions.append({
                            'title': title,
                            'location': location,
                            'url': url,
                            'posted_date': datetime.now(),  # Google doesn't show posted date on list
                            'description': '',
                            'requirements': []
                        })
                        
                    except Exception as e:
                        print(f"  ⚠️  Error parsing job card: {e}")
                        continue
                
                browser.close()
                print(f"  ✓ Extracted {len(positions)} internship positions")
        
        except Exception as e:
            print(f"  ✗ Error scraping {self.company_name}: {e}")
        
        return positions