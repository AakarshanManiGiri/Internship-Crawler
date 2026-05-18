from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import requests
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging for scrapers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseScraper(ABC):
    """Base class that all company scrapers must inherit from"""
    
    # Class-level statistics
    _stats = {}
    
    def __init__(self):
        self.company_name = self.get_company_name()
        self.careers_url = self.get_careers_url()
        self.enabled = True
        self.logger = logging.getLogger(f"scraper.{self.company_name}")
        
        # Shared requests session for all scrapers with retries and a default User-Agent
        self.session = self._create_session()
        
        # Health tracking
        if self.company_name not in BaseScraper._stats:
            BaseScraper._stats[self.company_name] = {
                'total_runs': 0,
                'successful_runs': 0,
                'total_jobs_found': 0,
                'last_run': None,
                'last_error': None
            }
    
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
        """Create a requests.Session configured with retries and sensible headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'InternshipCrawler/1.0 (+https://example.com)'
        })

        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('https://', adapter)
        session.mount('http://', adapter)

        return session
    
    def _record_success(self, job_count: int):
        """Record successful scrape run"""
        stats = BaseScraper._stats[self.company_name]
        stats['total_runs'] += 1
        stats['successful_runs'] += 1
        stats['total_jobs_found'] += job_count
        stats['last_run'] = datetime.now().isoformat()
        self.logger.info(f"✓ Scrape successful - Found {job_count} positions")
    
    def _record_error(self, error: str):
        """Record failed scrape run"""
        stats = BaseScraper._stats[self.company_name]
        stats['total_runs'] += 1
        stats['last_run'] = datetime.now().isoformat()
        stats['last_error'] = error
        self.logger.error(f"✗ Scrape failed - {error}")
    
    @classmethod
    def get_health_stats(cls) -> Dict:
        """Get health statistics for all scrapers"""
        return cls._stats.copy()