from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class VirtualVocationsScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Virtual Vocations Search URL
        # https://www.virtualvocations.com/jobs/q-python
        url = f"https://www.virtualvocations.com/jobs/q-{role.replace(' ', '+')}"
        logger.info(f"Navigating to Virtual Vocations: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job cards
            cards = await self.page.locator("div.job-card").all()
            if not cards:
                 cards = await self.page.locator("li.vv-job-list-item").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Virtual Vocations")

            for card in cards:
                try:
                    title_el = card.locator("a.job-link").first
                    if await title_el.count() == 0:
                         title_el = card.locator("h2 a").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    
                    # Company is often hidden
                    company = "Virtual Vocations Listing"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://www.virtualvocations.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company,
                        "location": "Remote",
                        "url": full_link,
                        "source": "Virtual Vocations"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Virtual Vocations: {e}")
            
        return jobs
