from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class MonsterScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        url = f"https://www.monster.com/jobs/search?q={role}&where={location}"
        
        logger.info(f"Navigating to Monster: {url}")
        await self.browser_manager.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Monster selectors (approximate, based on typical structure)
            cards = await self.page.locator("div[data-component='job-card']").all()
            if not cards:
                 # Fallback for newer Monster UI
                 cards = await self.page.locator("article").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Monster")
            
            for card in cards:
                try:
                    title_el = card.locator("a[data-test-id='svx-job-title']").first
                    if await title_el.count() == 0:
                         title_el = card.locator("h3").first
                    
                    title = await title_el.text_content() if await title_el.count() > 0 else "Unknown Title"
                    
                    company_el = card.locator("span[data-test-id='svx-job-company']").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown Company"
                    
                    location_el = card.locator("span[data-test-id='svx-job-location']").first
                    loc = await location_el.text_content() if await location_el.count() > 0 else "Unknown Location"
                    
                    url_el = card.locator("a").first
                    link = await url_el.get_attribute("href")
                    
                    if title != "Unknown Title":
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": loc.strip(),
                            "url": link,
                            "source": "Monster"
                        })
                        logger.debug(f"Extracted: {title.strip()} at {company.strip()}")
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Monster: {e}")
            
        return jobs
