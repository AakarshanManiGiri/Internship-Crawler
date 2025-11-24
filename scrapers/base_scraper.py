from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

class BaseScraper(ABC):
    """Base class that all company scrapers must inherit from"""
    
    def __init__(self):
        self.company_name = self.get_company_name()
        self.careers_url = self.get_careers_url()
        self.enabled = True
    
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