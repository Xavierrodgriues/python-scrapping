from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class TheLaddersScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # TheLadders Search URL
        # https://www.theladders.com/jobs/search-results?keywords=Python
        url = f"https://www.theladders.com/jobs/search-results?keywords={role.replace(' ', '+')}"
        logger.info(f"Navigating to TheLadders: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job structure
            # usually div.job-card-container
            cards = await self.page.locator("div.job-card-container").all()
            
            logger.info(f"Found {len(cards)} potential job cards on TheLadders")

            for card in cards:
                try:
                    title_el = card.locator("a.job-card-title").first
                    company_el = card.locator("a.job-card-company").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://www.theladders.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "TheLadders"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping TheLadders: {e}")
            
        return jobs
