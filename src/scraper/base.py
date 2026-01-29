from abc import ABC, abstractmethod
from typing import List, Dict
from loguru import logger
from src.core.browser import BrowserManager
from src.core.utils import human_delay

class BaseScraper(ABC):
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.page = None

    async def initialize(self):
        """Ensure page is ready."""
        # Request a dedicated page for this scraper instance
        self.page = await self.browser_manager.get_new_page()

    async def handle_blockers(self):
        """Generic blocker/popup handler."""
        if not self.page:
            return

        try:
            # 1. Check for Cloudflare / Generic Captcha titles
            title = await self.page.title()
            if "Cloudflare" in title or "Just a moment" in title or "Access Denied" in title:
                logger.warning(f"Potential blocker detected (Title: {title}). Waiting longer...")
                await human_delay(5.0, 10.0)
                
            # 2. Keypress Escape (closes many modals)
            await self.page.keyboard.press("Escape")
            await human_delay(0.5, 1.0)

            # 3. Common Close Buttons
            common_selectors = [
                 "button[aria-label='close']", 
                 "button[aria-label='Close']",
                 ".modal-close", 
                 ".close-btn",
                 "[data-testid='close-button']",
                 # ZipRecruiter specific (sometimes)
                 "a.modal_close",
                 "button.modal_close"
            ]
            
            for selector in common_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                         logger.info(f"Attempting to click close button: {selector}")
                         await self.page.locator(selector).first.click(timeout=1000)
                         await human_delay(0.5, 1.0)
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"Blocker check failed (non-critical): {e}")

    async def navigate(self, url: str):
        """Navigate to a URL using the scraper's page."""
        if not self.page:
            logger.error("Scraper page not initialized!")
            return
            
        logger.info(f"Navigating to {url}")
        try:
            # Reduced timeout to 30s to fail fast
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise

    @abstractmethod
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        """Search for jobs and return a list of job data dictionaries."""
        pass
