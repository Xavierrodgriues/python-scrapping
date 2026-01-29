from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class WeWorkRemotelyScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        
        # WeWorkRemotely Search URL
        base_url = f"https://weworkremotely.com/remote-jobs/search?term={role.replace(' ', '+')}"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            url = f"{base_url}&page={current_page}" if current_page > 1 else base_url
            
            logger.info(f"Navigating to WeWorkRemotely page {current_page}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"WeWorkRemotely navigation failed: {e}")
                break
                
            await human_delay(2.0, 4.0)
            
            jobs = await self._scrape_current_page(current_page)
            all_jobs.extend(jobs)
            
            if not jobs:
                logger.info("No jobs found on this page, stopping.")
                break
            
            logger.info(f"Extracted {len(jobs)} jobs from WeWorkRemotely page {current_page}")
            
            current_page += 1
            await human_delay(2.0, 3.0)
        
        logger.info(f"Total jobs scraped from WeWorkRemotely: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        try:
            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Check if jobs exist
            articles = await self.page.locator("section.jobs article").all()
            if not articles or len(articles) == 0:
                articles = await self.page.locator("li.feature").all()

            logger.info(f"Found {len(articles)} potential job cards on WeWorkRemotely page {page_num}")

            for article in articles:
                try:
                    title_el = article.locator("span.title").first
                    company_el = article.locator("span.company").first
                    
                    if await title_el.count() == 0:
                        continue
                    
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link_el = article.locator("a").first
                    link = await link_el.get_attribute("href") if await link_el.count() > 0 else None
                    
                    # WWR links are relative
                    full_link = f"https://weworkremotely.com{link}" if link and not link.startswith("http") else link

                    if title and full_link:
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": "Remote",
                            "url": full_link,
                            "source": "WeWorkRemotely",
                            "page": page_num
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping WeWorkRemotely page {page_num}: {e}")
            
        return jobs
