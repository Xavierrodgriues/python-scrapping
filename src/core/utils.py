import asyncio
import random
import sys
from loguru import logger
from pathlib import Path

def setup_logging(log_dir: str = "logs"):
    """Configure logging with rotation and helpful formatting."""
    Path(log_dir).mkdir(exist_ok=True)
    
    logger.remove()
    logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.add(f"{log_dir}/scraper.log", rotation="10 MB", retention="5 days", level="DEBUG")
    
    return logger

async def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """Sleep for a random amount of time to mimic human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Sleeping for {delay:.2f} seconds...")
    await asyncio.sleep(delay)

async def scroll_page(page, steps: int = 5, delay_min: float = 0.5, delay_max: float = 1.5):
    """Scroll the page down in steps to trigger lazy loading."""
    logger.info("Scrolling page...")
    for _ in range(steps):
        await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
        await human_delay(delay_min, delay_max)
    
    # Scroll back up a bit sometimes?
    if random.random() > 0.7:
        await page.evaluate("window.scrollBy(0, -window.innerHeight * 0.5)")
        await human_delay(0.5, 1.0)
