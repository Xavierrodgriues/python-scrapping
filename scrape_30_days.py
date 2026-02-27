import asyncio
import yaml
from loguru import logger
from src.core.browser import BrowserManager
from src.core.utils import setup_logging
from src.storage.writer import JobWriter
from src.storage.mongo import MongoWriter

import argparse

async def run_scraper(scraper, variation, location, mongo_writer, all_jobs, cat_name):
    """Worker function to run a single scraper with a 30-day filter."""
    scraper_name = scraper.__class__.__name__
    logger.info(f"Starting {scraper_name} for {variation} (30-day filter)...")
    try:
        # Pass mongo_writer and category so scraper can save incrementally
        # HARDCODED: days_old=30
        jobs = await scraper.search_jobs(
            variation, location, 
            days_old=30, 
            max_pages=15, # Increased max_pages slightly to accommodate more history
            mongo_writer=mongo_writer,
            category=cat_name
        )
        
        # Also save at the end in case scraper doesn't do incremental saves
        if jobs:
            for job in jobs:
                job["category"] = cat_name
            mongo_writer.upsert_jobs(jobs)
            # Also save to job_links collection with standardized format
            mongo_writer.save_job_links(jobs, role=variation)
        
        all_jobs.extend(jobs)
        logger.success(f"Found {len(jobs)} jobs for {variation} in {location} on {scraper_name}")
        
    except Exception as e:
        logger.error(f"Failed processing {variation} in {location} on {scraper_name}: {e}")
    finally:
        # Ideally close the page here to free resources
        if scraper.page:
            try:
                await scraper.page.close()
            except:
                pass

async def run():
    parser = argparse.ArgumentParser(description="Run scrapers with a 30-day time filter")
    parser.add_argument("--config", default="config/search_config.yaml", help="Path to configuration file")
    parser.add_argument("--scrapers", default=None, help="Comma-separated list of scrapers to run (e.g., 'IndeedScraper,RemoteOKScraper')")
    args = parser.parse_args()

    # Load config
    with open(args.config, "r") as f:
        search_config = yaml.safe_load(f)
        
    global_config = {}
    with open("config/settings.yaml", "r") as f:
        global_config = yaml.safe_load(f)

    # Setup logging
    setup_logging(global_config.get("paths", {}).get("logs_dir", "logs"))
    
    # Singleton Browser Manager (Persistent Context)
    browser_manager = BrowserManager()
    writer = JobWriter(global_config.get("paths", {}).get("data_dir", "data"))
    mongo_writer = MongoWriter() # Initialize MongoDB writer
    
    all_jobs = []
    
    try:
        await browser_manager.start()
        
        # Dynamic discovery
        import pkgutil
        import importlib
        import inspect
        import src.scraper
        from src.scraper.base import BaseScraper

        # Load scraper classes first (don't instantiate yet)
        scraper_classes = []
        package_path = src.scraper.__path__
        prefix = src.scraper.__name__ + "."
        
        target_scrapers = None
        if args.scrapers:
            target_scrapers = [s.strip().lower() for s in args.scrapers.split(",")]

        for _, name, _ in pkgutil.iter_modules(package_path, prefix):
            try:
                module = importlib.import_module(name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseScraper) and obj is not BaseScraper:
                        if target_scrapers and obj.__name__.lower() not in target_scrapers:
                            continue
                        scraper_classes.append(obj)
            except Exception as e:
                logger.error(f"Failed to load module {name}: {e}")

        logger.info(f"Loaded {len(scraper_classes)} scraper classes.")
        
        categories = search_config.get("categories", [])
        filters = search_config.get("filters", {})
        location = filters.get("location", "USA")
        
        # Process Categories
        for category in categories:
            cat_name = category.get("name")
            roles = category.get("roles", [])
            
            logger.info(f"Processing Category: {cat_name} (30 DAYS)")
            
            for role in roles:
                # PARALLEL EXECUTION STRATEGY:
                # Run scrapers in parallel but with concurrency limits
                variation = role 
                logger.info(f"-- Parallel Batch for: {variation} --")
                
                # Limit concurrency to 5 tabs to prevent browser freezing
                semaphore = asyncio.Semaphore(5)
                
                async def sem_task(cls):
                    async with semaphore:
                        # Instantiate fresh scraper
                        scraper_instance = cls(browser_manager)
                        # Wrap in hard timeout of 180s per scraper (longer for 30 days)
                        try:
                            await asyncio.wait_for(
                                run_scraper(scraper_instance, variation, location, mongo_writer, all_jobs, cat_name),
                                timeout=180.0
                            )
                        except asyncio.TimeoutError:
                            logger.error(f"Scraper {cls.__name__} timed out after 180s.")
                            # Attempt clean close
                            if scraper_instance.page:
                                try:
                                    await scraper_instance.page.close()
                                except: pass
                        except Exception as e:
                            logger.error(f"Error in scraper task {cls.__name__}: {e}")

                tasks = [asyncio.create_task(sem_task(cls)) for cls in scraper_classes]
                
                if tasks:
                    await asyncio.gather(*tasks)
                    
                    # Small delay between batches to be nice
                    await asyncio.sleep(2)

    except Exception as e:
        logger.critical(f"Critical error: {e}")
    finally:
        await browser_manager.close()
        
    # Save cumulative results to local files
    if all_jobs:
        logger.info(f"Total jobs found across all categories (30 days): {len(all_jobs)}")
        writer.save_jobs(all_jobs)
    else:
        logger.warning("No jobs found across all sources.")

if __name__ == "__main__":
    asyncio.run(run())
