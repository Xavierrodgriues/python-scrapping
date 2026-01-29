from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class DribbbleScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Dribbble Search URL
        # https://dribbble.com/jobs?keyword=Product+Designer&location=
        url = f"https://dribbble.com/jobs?keyword={role.replace(' ', '+')}"
        if location and location.lower() != "remote":
            url += f"&location={location.replace(' ', '+')}"
            
        logger.info(f"Navigating to Dribbble: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job cards
            # a.job-list-item
            cards = await self.page.locator("a.job-list-item").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Dribbble")

            for card in cards:
                try:
                    title_el = card.locator("p.job-title").first
                    company_el = card.locator("p.company-name").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await card.get_attribute("href")
                    full_link = f"https://dribbble.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "Dribbble"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Dribbble: {e}")
            
        return jobs
