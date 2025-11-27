import requests
from bs4 import BeautifulSoup
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from typing import Dict, List
class MetaScraper(BaseScraper):
    
    def get_company_name(self) -> str:
        return "Meta"
    
    def get_careers_url(self) -> str:
        return "https://www.metacareers.com/jobs"
    
    def scrape(self) -> List[Dict]:
        """Scrape Meta's careers page"""
        positions = []
        
        try:
            # Meta has a different structure - adapt accordingly
            response = requests.get(
                f"{self.careers_url}?q=intern",
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Example parsing (adjust selectors based on actual site)
            job_cards = soup.select('.job-card')
            
            for card in job_cards:
                title = card.select_one('.job-title').text.strip()
                
                if self.is_internship(title):
                    positions.append({
                        'title': title,
                        'location': card.select_one('.job-location').text.strip(),
                        'url': card.select_one('a')['href'],
                        'posted_date': datetime.now(),  # Parse from page if available
                        'description': card.select_one('.job-description').text.strip() if card.select_one('.job-description') else '',
                        'requirements': []
                    })
        
        except Exception as e:
            print(f"Error scraping {self.company_name}: {e}")
        
        return positions