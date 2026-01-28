import asyncio
import yaml
from loguru import logger
from src.core.browser import BrowserManager
from src.core.utils import setup_logging
from src.storage.writer import JobWriter
from src.storage.mongo import MongoWriter
from src.scraper.indeed import IndeedScraper
from src.scraper.linkedin import LinkedinScraper
from src.scraper.glassdoor import GlassdoorScraper
from src.scraper.monster import MonsterScraper
from src.scraper.google_jobs import GoogleJobsScraper

import argparse

async def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/search_config.yaml", help="Path to configuration file")
    args = parser.parse_args()

    # Load config
    with open(args.config, "r") as f:
        search_config = yaml.safe_load(f)
        
    global_config = {}
    with open("config/settings.yaml", "r") as f:
        global_config = yaml.safe_load(f)

    # Setup logging
    setup_logging(global_config.get("paths", {}).get("logs_dir", "logs"))
    
    browser_manager = BrowserManager()
    writer = JobWriter(global_config.get("paths", {}).get("data_dir", "data"))
    mongo_writer = MongoWriter() # Initialize MongoDB writer
    
    all_jobs = []
    
    try:
        await browser_manager.start()
        
        scrapers = [
            IndeedScraper(browser_manager),
            LinkedinScraper(browser_manager),
            GlassdoorScraper(browser_manager),
            MonsterScraper(browser_manager),
            GoogleJobsScraper(browser_manager)
        ]
        
        categories = search_config.get("categories", [])
        filters = search_config.get("filters", {})
        location = filters.get("location", "USA")
        
        # Calculate max pages or deep scrape flag? 
        # For now, we rely on scrapers' internal pagination limits or explicit kwargs if we add them.
        # User requested "fetch every page".
        
        for category in categories:
            cat_name = category.get("name")
            roles = category.get("roles", [])
            
            logger.info(f"Processing Category: {cat_name}")
            
            for role in roles:
                for scraper in scrapers:
                    scraper_name = scraper.__class__.__name__
                    logger.info(f"Searching for {role} in {location} on {scraper_name}...")
                    
                    try:
                        # Pass explicit date filter if supported by scraper impl
                        # We haven't fully implemented dynamic date filtering in individual scrapers yet,
                        # but we can pass it in kwargs for future expansion.
                        jobs = await scraper.search_jobs(role, location, days_old=30)
                        
                        # Enrich with category
                        for job in jobs:
                            job["category"] = cat_name
                            
                        # Save incrementally to MongoDB to avoid data loss
                        mongo_writer.upsert_jobs(jobs)
                        
                        all_jobs.extend(jobs)
                        logger.success(f"Found {len(jobs)} jobs for {role} in {location} on {scraper_name}")
                        
                    except Exception as e:
                        logger.error(f"Failed processing {role} in {location} on {scraper_name}: {e}")
                        
    except Exception as e:
        logger.critical(f"Critical error: {e}")
    finally:
        await browser_manager.close()
        
    # Save cumulative results to local files
    if all_jobs:
        logger.info(f"Total jobs found across all categories: {len(all_jobs)}")
        writer.save_jobs(all_jobs)
    else:
        logger.warning("No jobs found across all sources.")

if __name__ == "__main__":
    asyncio.run(run())
