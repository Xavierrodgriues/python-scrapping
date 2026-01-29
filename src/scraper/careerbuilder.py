from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class CareerBuilderScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # CareerBuilder Search URL
        # posted: 30 (days)
        url = f"https://www.careerbuilder.com/jobs?keywords={role.replace(' ', '+')}&location={location.replace(' ', '+')}&posted=30"
        logger.info(f"Navigating to CareerBuilder: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job structure often uses data-id or list items
            # Select parent blocks
            cards = await self.page.locator("div.data-results-content-parent").all()
            if not cards:
                 # Backup
                 cards = await self.page.locator("li.data-results-content").all()

            logger.info(f"Found {len(cards)} potential job cards on CareerBuilder")

            for card in cards:
                try:
                    title_el = card.locator("div.data-results-title").first
                    company_el = card.locator("div.data-details span").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    # URL usually on title parent or similar
                    # Sometimes extracted from data attributes, but usually an <a> is present
                    link_el = card.locator("a.data-results-content-click").first
                    # Fallback to searching inside title
                    if await link_el.count() == 0:
                         link_el = title_el.locator("xpath=..")
                    
                    link = await link_el.get_attribute("href")
                    full_link = f"https://www.careerbuilder.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "CareerBuilder"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping CareerBuilder: {e}")
            
        return jobs
