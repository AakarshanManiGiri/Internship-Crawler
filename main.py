from datetime import datetime
import importlib
import logging
from pathlib import Path
from database.db import Database
from services.notification_service import NotificationService
from scrapers.base_scraper import BaseScraper
from models.internship import Internship

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_health_report():
    """Log the current scraper health summary."""
    stats = BaseScraper.get_health_stats()

    if not stats:
        logger.info("No scraper health stats available yet.")
        return

    logger.info("\n" + "=" * 70)
    logger.info("SCRAPER HEALTH")
    logger.info("=" * 70)

    for company, data in stats.items():
        logger.info(
            "%s: %s/%s successful runs, %s jobs found, last run=%s",
            company,
            data.get('successful_runs', 0),
            data.get('total_runs', 0),
            data.get('total_jobs_found', 0),
            data.get('last_run') or 'never'
        )

        if data.get('last_error'):
            logger.info("%s last error: %s", company, data['last_error'])


class CrawlerManager:
    def __init__(self):
        self.db = Database()
        self.notification_service = NotificationService()
        self.scrapers = []
        logger.info("Initializing CrawlerManager")
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
                            logger.info(f"✓ Loaded scraper: {scraper_instance.company_name}")
                        else:
                            logger.info(f"⊘ Scraper disabled: {scraper_instance.company_name}")
            
            except Exception as e:
                logger.error(f"Error loading scraper {file.name}: {e}", exc_info=True)
    
    def run_crawl(self):
        """Run all scrapers and process results"""
        start_time = datetime.now()
        logger.info("=" * 70)
        logger.info(f"Starting crawl at {start_time}")
        logger.info("=" * 70)
        
        if not self.scrapers:
            logger.warning("No scrapers loaded!")
            return
        
        new_internships = []
        scrapers_run = 0
        scrapers_failed = 0
        
        for scraper in self.scrapers:
            try:
                logger.info(f"\n→ Crawling {scraper.company_name}...")
                positions = scraper.scrape()
                scrapers_run += 1
                
                logger.info(f"  Processing {len(positions)} positions from {scraper.company_name}")
                
                for position in positions:
                    try:
                        internship = Internship(
                            company=scraper.company_name,
                            **position
                        )
                        
                        internship_id = self.db.save_internship(internship)
                        if internship_id:
                            internship.id = internship_id
                            new_internships.append(internship)
                            logger.debug(f"  ✓ Saved: {internship.title}")
                        else:
                            logger.debug(f"  ⊘ Duplicate: {internship.title}")
                    
                    except Exception as e:
                        logger.warning(f"  ✗ Error saving internship: {e}")
                        continue
            
            except Exception as e:
                scrapers_failed += 1
                logger.error(f"✗ Scraper {scraper.company_name} failed: {e}", exc_info=True)
                continue
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "=" * 70)
        logger.info("CRAWL SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Elapsed Time: {elapsed:.1f} seconds")
        logger.info(f"Scrapers Run: {scrapers_run}/{len(self.scrapers)}")
        logger.info(f"Scrapers Failed: {scrapers_failed}")
        logger.info(f"New Internships Found: {len(new_internships)}")
        
        # Send notifications
        if new_internships:
            try:
                users = self.db.get_all_users()
                logger.info(f"\n→ Notifying {len(users)} user(s)...")
                
                self.notification_service.notify_new_internships(new_internships, users)
                
                # Mark as notified
                self.db.mark_as_notified([i.id for i in new_internships])
                logger.info("✓ Notifications sent!")
            
            except Exception as e:
                logger.error(f"Error sending notifications: {e}", exc_info=True)
        
        logger.info(f"\nCrawl completed at {datetime.now()}")
        logger.info("=" * 70 + "\n")
        
        # Print health report
        print_health_report()


if __name__ == "__main__":
    try:
        manager = CrawlerManager()
        manager.run_crawl()
    except Exception as e:
        logger.critical(f"Fatal error in crawler: {e}", exc_info=True)
        raise
