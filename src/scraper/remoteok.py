from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class RemoteOKScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # RemoteOK Search URL
        url = f"https://remoteok.com/remote-{role.replace(' ', '-').lower()}-jobs"
        logger.info(f"Navigating to RemoteOK: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        await scroll_page(self.page, steps=3)
        
        jobs = []
        try:
            # Job rows are tr.job
            rows = await self.page.locator("tr.job").all()
            logger.info(f"Found {len(rows)} potential job cards on RemoteOK")

            for row in rows:
                try:
                    title_el = row.locator("h2[itemprop='title']").first
                    company_el = row.locator("h3[itemprop='name']").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    # URL is usually on the row itself or a link inside
                    # RemoteOK uses data-href on the row often, or a direct link class check
                    # We'll look for the apply button or the main link
                    
                    link = await row.get_attribute("data-href")
                    if not link:
                         # Try finding <a>
                         link_el = row.locator("a.preventLink").first
                         if await link_el.count() > 0:
                             link = await link_el.get_attribute("href")
                    
                    full_link = f"https://remoteok.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote",
                        "url": full_link,
                        "source": "RemoteOK"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping RemoteOK: {e}")
            
        return jobs
