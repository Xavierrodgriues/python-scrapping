from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class RemotiveScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Remotive Search URL
        url = f"https://remotive.com/remote-jobs/search?query={role.replace(' ', '+')}"
        logger.info(f"Navigating to Remotive: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            # Job list structure
            cards = await self.page.locator("ul.job-list li").all()
            logger.info(f"Found {len(cards)} potential job cards on Remotive")

            for card in cards:
                try:
                    # Skip if it's a category header or ad
                    if await card.get_attribute("class") == "job-list-header":
                        continue
                        
                    title_el = card.locator("a.job-1-title").first
                    company_el = card.locator("span.company").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://remotive.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote",
                        "url": full_link,
                        "source": "Remotive"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Remotive: {e}")
            
        return jobs
