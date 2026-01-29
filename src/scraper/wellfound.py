from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class WellfoundScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Wellfound (AngelList) Search URL
        # They are very strict on bots, might redirect to login
        url = f"https://wellfound.com/jobs?q={role.replace(' ', '+')}&l={location.replace(' ', '+')}"
        logger.info(f"Navigating to Wellfound: {url}")
        
        await self.navigate(url)
        await human_delay(4.0, 7.0)
        
        jobs = []
        try:
             # Check for login wall
            if "Log In" in await self.page.title():
                 logger.warning("Wellfound requires login. Skipping public scrape.")
                 return []

            await scroll_page(self.page, steps=3)
            
            # Job cards
            # Selectors vary, usually div.styles_component__...
            # We look for something generic
            cards = await self.page.locator("div[class*='JobCard']").all()
            if not cards:
                 cards = await self.page.locator("div[data-test='JobListItem']").all()

            logger.info(f"Found {len(cards)} potential job cards on Wellfound")

            for card in cards:
                try:
                    title_el = card.locator("h2").first
                    company_el = card.locator("h3").first # Heuristic
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link_el = card.locator("a").first
                    link = await link_el.get_attribute("href")
                    
                    full_link = f"https://wellfound.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "Wellfound"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Wellfound: {e}")
            
        return jobs
