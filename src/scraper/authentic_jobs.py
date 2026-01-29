from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class AuthenticJobsScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Authentic Jobs Search URL
        # https://authenticjobs.com/?s=designer
        url = f"https://authenticjobs.com/?s={role.replace(' ', '+')}"
        logger.info(f"Navigating to Authentic Jobs: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job structure
            # ul#jobList li
            cards = await self.page.locator("ul#jobList > li").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Authentic Jobs")

            for card in cards:
                try:
                    title_el = card.locator("h3").first
                    company_el = card.locator("h4.company").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link_el = card.locator("a.job-details-link").first
                    link = await link_el.get_attribute("href")
                    
                    # Usually full link
                    full_link = link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote", # Mostly remote
                        "url": full_link,
                        "source": "AuthenticJobs"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Authentic Jobs: {e}")
            
        return jobs
