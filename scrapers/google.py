import requests
from bs4 import BeautifulSoup
from datetime import datetime

from sympy import Dict, List
from scrapers.base_scraper import BaseScraper

class GoogleScraper(BaseScraper):
    
    def get_company_name(self) -> str:
        return "Google"
    
    def get_careers_url(self) -> str:
        return "https://www.google.com/about/careers/applications/jobs/results/"
    
    def scrape(self) -> List[Dict]:
        """Scrape Google's careers API"""
        positions = []
        
        try:
            # Google uses an API endpoint
            api_url = "https://www.google.com/about/careers/applications/jobs/results/"
            params = {
                'q': 'intern',
                'employment_type': 'INTERN'
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse response (adjust based on actual API structure)
            data = response.json()
            
            for job in data.get('jobs', []):
                if self.is_internship(job.get('title', '')):
                    positions.append({
                        'title': job.get('title'),
                        'location': ', '.join(job.get('locations', [])),
                        'url': f"https://www.google.com/about/careers/applications/jobs/results/{job.get('id')}",
                        'posted_date': datetime.fromisoformat(job.get('posted_date')),
                        'description': job.get('description', ''),
                        'requirements': job.get('qualifications', [])
                    })
        
        except Exception as e:
            print(f"Error scraping {self.company_name}: {e}")
        
        return positions