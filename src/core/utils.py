import asyncio
import random
import sys
from loguru import logger
from pathlib import Path
from typing import List

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

def get_role_variations(role: str) -> List[str]:
    """Expand a role into common variations for broader search coverage."""
    variations = {role} # Use set to avoid duplicates
    role_lower = role.lower()
    
    # Keyword based expansion
    if "backend" in role_lower:
        variations.add("Backend Developer")
        variations.add("Backend Software Engineer")
        variations.add("Software Engineer - Backend")
        variations.add("Server Side Engineer")
    
    if "frontend" in role_lower:
        variations.add("Frontend Developer")
        variations.add("Frontend Software Engineer")
        variations.add("UI Engineer")
        variations.add("Web Developer")
        variations.add("React Developer")
        
    if "full stack" in role_lower or "fullstack" in role_lower:
        variations.add("Full Stack Developer")
        variations.add("Full Stack Software Engineer")
        variations.add("Software Engineer - Full Stack")

    if "devops" in role_lower:
        variations.add("DevOps Engineer")
        variations.add("Site Reliability Engineer")
        variations.add("SRE")
        variations.add("Platform Engineer")
        variations.add("Cloud Engineer")
        
    if "data scientist" in role_lower:
        variations.add("Machine Learning Engineer")
        variations.add("AI Engineer")
        variations.add("Data Analyst")
        
    if "product manager" in role_lower:
        variations.add("Technical Product Manager")
        variations.add("Product Owner")
        
    # Generic mixins
    if "engineer" in role_lower and "software" not in role_lower:
        variations.add(role.replace("Engineer", "Developer"))
    if "developer" in role_lower:
        variations.add(role.replace("Developer", "Engineer"))

    return list(variations)
