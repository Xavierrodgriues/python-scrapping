from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class PowerToFlyScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # PowerToFly Search URL
        # https://powertofly.com/jobs/?keywords=Python&location=Remote
        url = f"https://powertofly.com/jobs/?keywords={role.replace(' ', '+')}"
        
        logger.info(f"Navigating to PowerToFly: {url}")
        
        await self.navigate(url)
        await human_delay(4.0, 6.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job cards
            # .job-card or similar
            cards = await self.page.locator("div.job-card").all()
            if not cards:
                 # Fallback
                 cards = await self.page.locator("div.card").all()

            logger.info(f"Found {len(cards)} potential job cards on PowerToFly")

            for card in cards:
                try:
                    title_el = card.locator("a.job-title").first
                    company_el = card.locator("a.company-name").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://powertofly.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "PowerToFly"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping PowerToFly: {e}")
            
        return jobs
