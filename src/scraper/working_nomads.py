from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class WorkingNomadsScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Working Nomads Search URL
        url = f"https://www.workingnomads.com/jobs?q={role.replace(' ', '+')}"
        logger.info(f"Navigating to Working Nomads: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        await scroll_page(self.page, steps=3)
        
        jobs = []
        try:
            # Job items
            cards = await self.page.locator("div.job-list > div a.job").all()
            logger.info(f"Found {len(cards)} potential job cards on Working Nomads")

            for card in cards:
                try:
                    title_el = card.locator("h4").first
                    company_el = card.locator("div.company").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await card.get_attribute("href")
                    full_link = f"https://www.workingnomads.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote",
                        "url": full_link,
                        "source": "Working Nomads"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Working Nomads: {e}")
            
        return jobs
