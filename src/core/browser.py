import asyncio
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
        self.page: Page = None

    def _load_config(self, path: str) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    async def start(self):
        """Initialize Playwright and Browser."""
        logger.info("Starting Browser Manager...")
        self.playwright = await async_playwright().start()
        
        browser_conf = self.config.get("browser", {})
        headless = browser_conf.get("headless", False)
        
        logger.debug(f"Launching browser (Headless: {headless})")
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ]
        )
        
        # Create context with realistic viewport and user agent
        self.context = await self.browser.new_context(
            viewport={"width": browser_conf.get("width", 1920), "height": browser_conf.get("height", 1080)},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.page = await self.context.new_page()
        
        # Apply stealth (v2 usage)
        stealth = Stealth()
        await stealth.apply_stealth_async(self.page)
        logger.info("Browser started and stealth mode enabled.")

    async def close(self):
        """Close all browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed.")
        except Exception as e:
            logger.warning(f"Error closing browser resources (likely already closed): {e}")

    async def navigate(self, url: str):
        """Navigate to a URL with error handling."""
        logger.info(f"Navigating to {url}")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise
