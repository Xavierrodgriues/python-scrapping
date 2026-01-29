from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class RemoteOKScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        
        # RemoteOK Search URL with pagination
        base_url = f"https://remoteok.com/remote-{role.replace(' ', '-').lower()}-jobs"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            # RemoteOK uses ?page= for pagination
            url = f"{base_url}?page={current_page}" if current_page > 1 else base_url
            
            logger.info(f"Navigating to RemoteOK page {current_page}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"RemoteOK navigation failed: {e}")
                break
                
            await human_delay(3.0, 5.0)
            
            jobs = await self._scrape_current_page(current_page)
            all_jobs.extend(jobs)
            
            if not jobs:
                logger.info("No jobs found on this page, stopping.")
                break
            
            logger.info(f"Extracted {len(jobs)} jobs from RemoteOK page {current_page}")
            
            current_page += 1
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from RemoteOK: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        try:
            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Job rows are tr.job
            rows = await self.page.locator("tr.job").all()
            logger.info(f"Found {len(rows)} potential job cards on RemoteOK page {page_num}")

            for row in rows:
                try:
                    title_el = row.locator("h2, .title").first
                    company_el = row.locator("h3, .company").first
                    
                    if await title_el.count() == 0:
                        continue
                    
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await row.get_attribute("data-href")
                    if not link:
                        link_el = row.locator("a.preventLink").first
                        if await link_el.count() > 0:
                            link = await link_el.get_attribute("href")
                    
                    full_link = f"https://remoteok.com{link}" if link and not link.startswith("http") else link

                    if title and full_link:
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": "Remote",
                            "url": full_link,
                            "source": "RemoteOK",
                            "page": page_num
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping RemoteOK page {page_num}: {e}")
            
        return jobs
