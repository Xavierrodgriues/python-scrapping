from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class LinkedinScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # LinkedIn Guest Search URL
        # f_TPR parameter: r2592000 = 30 days (in seconds)
        seconds = kwargs.get("days_old", 30) * 86400
        url = f"https://www.linkedin.com/jobs/search?keywords={role}&location={location}&f_TPR=r{seconds}"
        
        logger.info(f"Navigating to LinkedIn: {url}")
        await self.navigate(url)
        await human_delay(2.0, 4.0)
        
        jobs = []
        try:
            # Scroll to load more jobs
            await scroll_page(self.page, steps=4)
            
            # Select job cards
            # LinkedIn guest view usually uses a list with classes like 'jobs-search__results-list'
            cards = await self.page.locator("ul.jobs-search__results-list li").all()
            logger.info(f"Found {len(cards)} potential job cards on LinkedIn")
            
            for card in cards:
                try:
                    title_el = card.locator("h3.base-search-card__title").first
                    title = await title_el.text_content() if await title_el.count() > 0 else "Unknown Title"
                    
                    company_el = card.locator("h4.base-search-card__subtitle").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown Company"
                    
                    location_el = card.locator("span.job-search-card__location").first
                    loc = await location_el.text_content() if await location_el.count() > 0 else "Unknown Location"
                    
                    url_el = card.locator("a.base-card__full-link").first
                    link = await url_el.get_attribute("href")
                    
                    if title != "Unknown Title":
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": loc.strip(),
                            "url": link,
                            "source": "LinkedIn"
                        })
                        logger.debug(f"Extracted: {title.strip()} at {company.strip()}")
                        
                except Exception as e:
                    # Often some cards are just dividers or ads
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
            
        return jobs
