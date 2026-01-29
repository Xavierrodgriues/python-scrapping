from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class RemoteCoScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Remote.co Search URL
        # They have categories like /remote-co-jobs/developer/ or search functionality
        # Search URL: https://remote.co/remote-jobs/search/?search_keywords=Python
        
        url = f"https://remote.co/remote-jobs/search/?search_keywords={role.replace(' ', '+')}"
        logger.info(f"Navigating to Remote.co: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            # Job cards are usually a.card or similar structure
            cards = await self.page.locator("a.card").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Remote.co")

            for card in cards:
                try:
                    title_el = card.locator("span.font-weight-bold").first
                    company_el = card.locator("p.text-secondary").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    
                    # Company name often contains " | Time" or similar text, might need cleanup
                    raw_company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    company = raw_company.split("|")[0].strip()
                    
                    link = await card.get_attribute("href")
                    full_link = f"https://remote.co{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote",
                        "url": full_link,
                        "source": "Remote.co"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Remote.co: {e}")
            
        return jobs
