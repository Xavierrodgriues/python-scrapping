from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class SnagajobScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Snagajob Search URL
        # https://www.snagajob.com/search?q=Python&w=USA
        url = f"https://www.snagajob.com/search?q={role.replace(' ', '+')}"
        if location:
            url += f"&w={location.replace(' ', '+')}"
            
        logger.info(f"Navigating to Snagajob: {url}")
        
        await self.navigate(url)
        await human_delay(4.0, 6.0)
        
        jobs = []
        try:
            # Check for generic blockage
            if "Access Denied" in await self.page.title():
                 logger.warning("Snagajob blocked access.")
                 return []

            await scroll_page(self.page, steps=3)
            
            # Job cards
            # job-card or similar
            cards = await self.page.locator("job-card").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Snagajob")

            for card in cards:
                try:
                    # Snagajob uses shadow DOM often or custom elements
                    # We try to get text from columns
                    title_el = card.locator("h2").first
                    company_el = card.locator(".company-name").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    # Link might be on the card itself or internal anchor
                    link_el = card.locator("a").first
                    link = await link_el.get_attribute("href")
                    full_link = f"https://www.snagajob.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "Snagajob"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Snagajob: {e}")
            
        return jobs
