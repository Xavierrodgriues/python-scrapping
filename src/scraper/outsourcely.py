from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class OutsourcelyScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Outsourcely Search URL
        url = f"https://www.outsourcely.com/remote-jobs#!/?q={role.replace(' ', '+')}"
        logger.info(f"Navigating to Outsourcely: {url}")
        
        await self.navigate(url)
        await human_delay(4.0, 6.0) # SPA heavy
        
        jobs = []
        try:
            # Job structure
            cards = await self.page.locator("div.job-listing").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Outsourcely")

            for card in cards:
                try:
                    title_el = card.locator("div.job-title").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = "Outsourcely Client"
                    
                    # Links are often js-based or on the title
                    link_el = card.locator("a").first
                    link = await link_el.get_attribute("href")
                    full_link = f"https://www.outsourcely.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company,
                        "location": "Remote",
                        "url": full_link,
                        "source": "Outsourcely"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Outsourcely: {e}")
            
        return jobs
