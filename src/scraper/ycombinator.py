from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class YCombinatorScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # YC Work at a Startup
        # URL needs specific structure, often just global search
        url = f"https://www.workatastartup.com/companies?query={role.replace(' ', '+')}"
        logger.info(f"Navigating to Y Combinator: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        await scroll_page(self.page, steps=5) # Infinite scroll often
        
        jobs = []
        try:
            # Job structure
            # usually divs with class company-job or similar
            cards = await self.page.locator("div.company-card").all()
            
            logger.info(f"Found {len(cards)} potential company cards (grouping jobs) on YC")

            for card in cards:
                try:
                    company_el = card.locator("span.company-name").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    # Jobs are listed under the company card usually
                    job_links = await card.locator("a.job-name").all()
                    
                    for job_link in job_links:
                        title = await job_link.text_content()
                        link = await job_link.get_attribute("href")
                        full_link = f"https://www.workatastartup.com{link}" if link and not link.startswith("http") else link
                        
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": "Remote/Hybrid", # Often mixed
                            "url": full_link,
                            "source": "YCombinator"
                        })

                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Y Combinator: {e}")
            
        return jobs
