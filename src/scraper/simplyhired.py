from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class SimplyHiredScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # SimplyHired Search URL
        days = kwargs.get("days_old", 30)
        # SimplyHired date filter: fdb=30
        url = f"https://www.simplyhired.com/search?q={role.replace(' ', '+')}&l={location.replace(' ', '+')}&fdb={days}"
        logger.info(f"Navigating to SimplyHired: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        await scroll_page(self.page, steps=3)
        
        jobs = []
        try:
            # Job structure
            # Checks for li.SerpJob or div.SerpJob-jobCard
            cards = await self.page.locator("li.SerpJob").all()
            if not cards:
                 cards = await self.page.locator("div.SerpJob-jobCard").all()

            logger.info(f"Found {len(cards)} potential job cards on SimplyHired")

            for card in cards:
                try:
                    title_el = card.locator("a.SerpJob-link").first
                    company_el = card.locator("span.JobPosting-labelWithIcon").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await title_el.get_attribute("href")
                    # Links are usually relative
                    full_link = f"https://www.simplyhired.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "SimplyHired"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping SimplyHired: {e}")
            
        return jobs
