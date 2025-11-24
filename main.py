from datetime import datetime
import importlib
import os
from pathlib import Path
from database.db import Database
from services.notification_service import NotificationService
from scrapers.base_scraper import BaseScraper
from models.internship import Internship

class CrawlerManager:
    def __init__(self):
        self.db = Database()
        self.notification_service = NotificationService()
        self.scrapers = []
        self._load_scrapers()
    
    def _load_scrapers(self):
        """Dynamically load all scraper modules"""
        scrapers_dir = Path("scrapers")
        
        for file in scrapers_dir.glob("*.py"):
            if file.name.startswith("_") or file.name == "base_scraper.py":
                continue
            
            module_name = f"scrapers.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                
                # Find the scraper class in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseScraper) and 
                        attr is not BaseScraper):
                        
                        scraper_instance = attr()
                        if scraper_instance.enabled:
                            self.scrapers.append(scraper_instance)
                            print(f"Loaded scraper: {scraper_instance.company_name}")
            
            except Exception as e:
                print(f"Error loading scraper {file.name}: {e}")
    
    def run_crawl(self):
        """Run all scrapers and process results"""
        print(f"\n{'='*50}")
        print(f"Starting crawl at {datetime.now()}")
        print(f"{'='*50}\n")
        
        new_internships = []
        
        for scraper in self.scrapers:
            print(f"Crawling {scraper.company_name}...")
            positions = scraper.scrape()
            
            for position in positions:
                internship = Internship(
                    company=scraper.company_name,
                    **position
                )
                
                internship_id = self.db.save_internship(internship)
                if internship_id:
                    internship.id = internship_id
                    new_internships.append(internship)
                    print(f"  ✓ New: {internship.title}")
        
        print(f"\nFound {len(new_internships)} new internship(s)")
        
        # Send notifications
        if new_internships:
            users = self.db.get_all_users()
            print(f"Notifying {len(users)} user(s)...")
            
            self.notification_service.notify_new_internships(new_internships, users)
            
            # Mark as notified
            self.db.mark_as_notified([i.id for i in new_internships])
            print("Notifications sent!")
        
        print(f"\n{'='*50}")
        print(f"Crawl completed at {datetime.now()}")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    manager = CrawlerManager()
    manager.run_crawl()