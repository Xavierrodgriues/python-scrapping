from abc import ABC, abstractmethod
from typing import List, Dict
from src.core.browser import BrowserManager

class BaseScraper(ABC):
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.page = None

    async def initialize(self):
        """Ensure page is ready."""
        if not self.browser_manager.page:
            await self.browser_manager.start()
        self.page = self.browser_manager.page

    @abstractmethod
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        """Search for jobs and return a list of job data dictionaries."""
        pass
