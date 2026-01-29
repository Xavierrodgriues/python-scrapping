from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class JobspressoScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Jobspresso Search URL
        url = f"https://jobspresso.co/?s={role.replace(' ', '+')}"
        logger.info(f"Navigating to Jobspresso: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job listings
            cards = await self.page.locator("div.job_listing").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Jobspresso")

            for card in cards:
                try:
                    title_el = card.locator("h3.job_listing-title").first
                    company_el = card.locator("div.job_listing-company strong").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link_el = card.locator("a").first
                    link = await link_el.get_attribute("href")
                    
                    full_link = link # Jobspresso links are full

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote",
                        "url": full_link,
                        "source": "Jobspresso"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Jobspresso: {e}")
            
        return jobs
