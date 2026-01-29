from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class HubstaffScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Hubstaff Talent Search URL
        url = f"https://talent.hubstaff.com/search/jobs?search_term={role.replace(' ', '+')}"
        logger.info(f"Navigating to Hubstaff Talent: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        await scroll_page(self.page, steps=3)
        
        jobs = []
        try:
            # Job cards
            cards = await self.page.locator("a.search-result").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Hubstaff Talent")

            for card in cards:
                try:
                    title_el = card.locator("div.name").first
                    company_el = card.locator("div.agency-name").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Hubstaff Client"
                    
                    link = await card.get_attribute("href")
                    full_link = link # Usually absolute or relative? Check.
                    # Usually absolute on Hubstaff
                    if link and not link.startswith("http"):
                        full_link = f"https://talent.hubstaff.com{link}"

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote",
                        "url": full_link,
                        "source": "Hubstaff"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Hubstaff Talent: {e}")
            
        return jobs
