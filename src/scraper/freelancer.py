from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class FreelancerScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Freelancer Search URL
        # https://www.freelancer.com/jobs/python/
        # Or search param: https://www.freelancer.com/jobs/?keyword=python
        url = f"https://www.freelancer.com/jobs/?keyword={role.replace(' ', '+')}"
        logger.info(f"Navigating to Freelancer.com: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job cards
            # .JobSearchCard-item or similar
            cards = await self.page.locator("div.JobSearchCard-item").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Freelancer")

            for card in cards:
                try:
                    title_el = card.locator("a.JobSearchCard-primary-heading-link").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = "Freelancer Client"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://www.freelancer.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company,
                        "location": "Remote",
                        "url": full_link,
                        "source": "Freelancer"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Freelancer: {e}")
            
        return jobs
