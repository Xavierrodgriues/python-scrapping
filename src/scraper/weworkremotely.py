from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class WeWorkRemotelyScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # We Work Remotely Search URL
        url = f"https://weworkremotely.com/remote-jobs/search?term={role.replace(' ', '+')}"
        logger.info(f"Navigating to We Work Remotely: {url}")
        
        await self.navigate(url)
        await human_delay(2.0, 4.0)
        
        jobs = []
        try:
            # Check if jobs exist
            articles = await self.page.locator("section.jobs article").all()
            if not articles:
                 # Backup selector for search result list
                 articles = await self.page.locator("li.feature").all()

            logger.info(f"Found {len(articles)} potential job cards on WeWorkRemotely")

            for article in articles:
                try:
                    # Sometimes structure varies between sections
                    
                    title_el = article.locator("span.title").first
                    company_el = article.locator("span.company").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    # Links are usually on the parent <a> or inside
                    link_el = article.locator("a").first
                    if await link_el.count() == 0:
                         # Try finding link in parent li if we are searching lis
                         pass
                    
                    link = await link_el.get_attribute("href")
                    # WWR links are relative
                    full_link = f"https://weworkremotely.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote", # WWR is purely remote
                        "url": full_link,
                        "source": "WeWorkRemotely"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping WeWorkRemotely: {e}")
            
        return jobs
