from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class NexxtScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Nexxt Search URL
        # https://www.nexxt.com/jobs/search?q=Python&l=USA
        url = f"https://www.nexxt.com/jobs/search?q={role.replace(' ', '+')}&l={location.replace(' ', '+')}"
        logger.info(f"Navigating to Nexxt: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job cards
            # div.result-card
            cards = await self.page.locator("div.result-card").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Nexxt")

            for card in cards:
                try:
                    title_el = card.locator("a.job-title").first
                    company_el = card.locator("a.company-name").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await title_el.get_attribute("href")
                    # Usually full or relative
                    full_link = f"https://www.nexxt.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "Nexxt"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Nexxt: {e}")
            
        return jobs
