from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class DiceScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Dice Search URL
        days = "Today" if kwargs.get("days_old", 30) <= 1 else "Last30Days" # Dice filter logic 
        # But filter param is complicated, sticking to generic mostly
        url = f"https://www.dice.com/jobs?q={role.replace(' ', '+')}&location={location.replace(' ', '+')}"
        logger.info(f"Navigating to Dice: {url}")
        
        await self.navigate(url)
        await human_delay(4.0, 7.0) # Dice is heavy SPA
        
        jobs = []
        try:
            # Check blockage
            title = await self.page.title()
            if "Access Denied" in title or "Security" in title:
                 logger.warning("Dice blocked access. Skipping.")
                 return []
            
            await scroll_page(self.page, steps=3)
            
            # Job cards are usually dhi-search-card or similar
            cards = await self.page.locator("dhi-search-card").all()
            if not cards:
                # Fallback to general card class
                cards = await self.page.locator(".card").all()
                
            logger.info(f"Found {len(cards)} potential job cards on Dice")

            for card in cards:
                try:
                    title_el = card.locator("a.card-title-link").first
                    company_el = card.locator("a.card-company-link").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await title_el.get_attribute("href")
                    
                    # Dice links are usually absolute, but verify
                    full_link = f"https://www.dice.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "Dice"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Dice: {e}")
            
        return jobs
