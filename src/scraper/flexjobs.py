from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class FlexJobsScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # FlexJobs Search URL
        # e.g., https://www.flexjobs.com/search?search=python
        url = f"https://www.flexjobs.com/search?search={role.replace(' ', '+')}"
        if location and location.lower() != "remote":
             url += f"&location={location.replace(' ', '+')}"
             
        logger.info(f"Navigating to FlexJobs: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        await scroll_page(self.page, steps=3)
        
        jobs = []
        try:
            # Job items
            # Usually li.list-group-item or div.job
            cards = await self.page.locator("li[data-job-id]").all()
            
            logger.info(f"Found {len(cards)} potential job cards on FlexJobs")

            for card in cards:
                try:
                    title_el = card.locator("a.job-title").first
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    
                    # FlexJobs hides company names for non-members mostly, sometimes shows "Reputable Company"
                    # We preserve what we can find
                    company = "Confidential/FlexJobs"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://www.flexjobs.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company,
                        "location": "Remote", # Primarily remote
                        "url": full_link,
                        "source": "FlexJobs"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping FlexJobs: {e}")
            
        return jobs
