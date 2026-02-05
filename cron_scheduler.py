
import schedule
import time
import subprocess
import sys
from datetime import datetime
from loguru import logger

# Configure logging
logger.add("logs/cron_scheduler.log", rotation="10 MB", retention="7 days")

def run_scraper():
    """Execute the main scraper."""
    logger.info(f"Starting scheduled scrape at {datetime.now()}")
    
    try:
        import os
        # Set PYTHONPATH so the subprocess can find the src module
        env = os.environ.copy()
        env["PYTHONPATH"] = "."

        # Run without capture_output=True so logs stream directly to the terminal
        result = subprocess.run(
            [sys.executable, "-m", "src.main"],
            cwd=".",
            env=env
        )
        
        if result.returncode == 0:
            logger.success("Scraper completed successfully")
        else:
            logger.error(f"Scraper failed with exit code {result.returncode}")
            
    except Exception as e:
        logger.error(f"Failed to run scraper: {e}")

# Schedule jobs at 1:07 AM and 1:07 PM daily
schedule.every().day.at("04:29").do(run_scraper)
schedule.every().day.at("13:54").do(run_scraper)

if __name__ == "__main__":
    logger.info("Cron scheduler started. Waiting for scheduled times (05:00 and 17:00)...")
    logger.info("Press Ctrl+C to stop.")
    
    # Optionally run immediately on startup
    run_scraper()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
