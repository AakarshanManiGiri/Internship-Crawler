from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BaseScraper(ABC):
    """Base class that all company scrapers must inherit from"""
    
    def __init__(self):
        self.company_name = self.get_company_name()
        self.careers_url = self.get_careers_url()
        self.enabled = True
        # Shared requests session for all scrapers with retries and a default User-Agent
        self.session = self._create_session()
    
    @abstractmethod
    def get_company_name(self) -> str:
        """Return the company name"""
        pass
    
    @abstractmethod
    def get_careers_url(self) -> str:
        """Return the careers page URL"""
        pass
    
    @abstractmethod
    def scrape(self) -> List[Dict]:
        """
        Scrape internship positions and return standardized data
        
        Returns:
            List of dicts with keys:
            - title: str
            - location: str
            - url: str
            - posted_date: datetime
            - description: str (optional)
            - requirements: List[str] (optional)
        """
        pass
    
    def is_internship(self, title: str) -> bool:
        """Helper to check if a position is an internship"""
        keywords = ['intern', 'internship', 'co-op', 'coop', 'summer']
        return any(keyword in title.lower() for keyword in keywords)

    def _create_session(self) -> requests.Session:
        """Create a requests.Session configured with retries and sensible headers.

        This ensures scrapers share a common session config.
        """
        session = requests.Session()
        session.headers.update({'User-Agent': 'InternshipCrawler/1.0 (+https://example.com)'} )

        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('https://', adapter)
        session.mount('http://', adapter)

        return session