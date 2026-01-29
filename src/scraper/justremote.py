from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class JustRemoteScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # JustRemote Search URL
        # https://justremote.co/remote-jobs?item=Python
        url = f"https://justremote.co/remote-jobs?item={role.replace(' ', '+')}"
        logger.info(f"Navigating to JustRemote: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        await scroll_page(self.page, steps=3)
        
        jobs = []
        try:
            # Job items
            cards = await self.page.locator("div.job-item").all()
            
            logger.info(f"Found {len(cards)} potential job cards on JustRemote")

            for card in cards:
                try:
                    title_el = card.locator("h3").first # Assuming H3 for title based on common changes
                    if await title_el.count() == 0:
                         # Fallback
                         title_el = card.locator(".job-title").first

                    company_el = card.locator(".job-company").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    # Link is often on the wrapping anchor or a 'Apply' button
                    link_el = card.locator("a").first
                    link = await link_el.get_attribute("href")
                    
                    full_link = f"https://justremote.co{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote",
                        "url": full_link,
                        "source": "JustRemote"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping JustRemote: {e}")
            
        return jobs
