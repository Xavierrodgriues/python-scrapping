from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class UpworkScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Upwork Search URL
        # e.g., https://www.upwork.com/nx/jobs/search/?q=python
        # Upwork is extremely heavy on bot detection.
        url = f"https://www.upwork.com/nx/jobs/search/?q={role.replace(' ', '+')}"
        logger.info(f"Navigating to Upwork: {url}")
        
        await self.navigate(url)
        await human_delay(4.0, 7.0)
        
        jobs = []
        try:
             # Check for blocked access or login wall
            title = await self.page.title()
            if "Access Denied" in title or "Log In" in title:
                 logger.warning("Upwork detected bot or requires login. Skipping.")
                 return []

            await scroll_page(self.page, steps=3)
            
            # Job cards
            # Often section.up-card-section or similar
            cards = await self.page.locator("section.up-card-section").all()
            if not cards:
                cards = await self.page.locator("div.up-card-section").all()
                
            logger.info(f"Found {len(cards)} potential job cards on Upwork")

            for card in cards:
                try:
                    title_el = card.locator("h3.job-tile-title a").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    
                    # Upwork doesn't list company names publicly usually
                    company = "Upwork Client"
                    
                    link = await title_el.get_attribute("href")
                    
                    full_link = f"https://www.upwork.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company,
                        "location": "Remote", # Upwork is almost entirely remote
                        "url": full_link,
                        "source": "Upwork"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Upwork: {e}")
            
        return jobs
