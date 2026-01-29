from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class USAJobsScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # USAJobs Search URL
        # https://www.usajobs.gov/Search/Results?k=Python
        url = f"https://www.usajobs.gov/Search/Results?k={role.replace(' ', '%20')}"
        if location and location.lower() != "remote":
             url += f"&l={location.replace(' ', '%20')}"
             
        logger.info(f"Navigating to USAJobs: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job cards
            # .usajobs-search-result--core
            cards = await self.page.locator("div.usajobs-search-result--core").all()
            
            logger.info(f"Found {len(cards)} potential job cards on USAJobs")

            for card in cards:
                try:
                    title_el = card.locator("a.usajobs-search-result--core__title").first
                    dept_el = card.locator("div.usajobs-search-result--core__department").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await dept_el.text_content() if await dept_el.count() > 0 else "U.S. Government"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://www.usajobs.gov{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location or "USA",
                        "url": full_link,
                        "source": "USAJobs"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping USAJobs: {e}")
            
        return jobs
