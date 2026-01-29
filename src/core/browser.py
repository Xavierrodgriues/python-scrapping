import asyncio
import os
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from playwright_stealth import Stealth
from loguru import logger
import yaml

class BrowserManager:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        # self.page is removed in favor of get_new_page
        self.user_data_dir = os.path.abspath("browser_data")
        self.active_pages = []

    def _load_config(self, path: str) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    async def start(self):
        """Initialize Playwright and Browser with Persistent Context."""
        if self.context:
            return # Already started
            
        logger.info(f"Starting Browser Manager with persistence at: {self.user_data_dir}")
        self.playwright = await async_playwright().start()
        
        browser_conf = self.config.get("browser", {})
        headless = browser_conf.get("headless", False)
        
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-component-extensions-with-background-pages",
            "--disable-extensions",
            "--disable-features=Translate,BackForwardCache,AcceptCHFrame,MediaRouter,OptimizationHints",
            "--disable-ipc-flooding-protection",
            "--disable-renderer-backgrounding",
            "--enable-features=NetworkService,NetworkServiceInProcess"
        ]

        logger.debug(f"Launching persistent context (Headless: {headless})")
        
        # Use launch_persistent_context instead of launch
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=headless,
            channel="chrome", # Try specified channel
            args=args,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Context might have an initial page
        if self.context.pages:
            self.active_pages.extend(self.context.pages)

        logger.info("Browser started with persistence.")

    async def get_new_page(self) -> Page:
        """Create and return a new stealthy page in the context."""
        if not self.context:
            await self.start()
            
        page = await self.context.new_page()
        
        # Apply stealth (v2 usage)
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.active_pages.append(page)
        return page

    async def close(self):
        """Close all browser resources."""
        try:
            # Pages are closed when context closes, but good to be explicit if needed
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed.")
        except Exception as e:
            logger.warning(f"Error closing browser resources: {e}")

    async def navigate(self, page: Page, url: str): # Updated to take page arg
        """Navigate a specific page to a URL."""
        if not page:
            logger.error("No page provided for navigation")
            return

        logger.info(f"Navigating to {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise
