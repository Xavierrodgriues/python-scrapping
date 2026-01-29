from typing import List, Dict, Set
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class RemoteOKScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 3)  # Reduced - RemoteOK doesn't have true pagination
        mongo_writer = kwargs.get("mongo_writer")
        category = kwargs.get("category", "")
        
        # RemoteOK Search URL - single page, infinite scroll
        url = f"https://remoteok.com/remote-{role.replace(' ', '-').lower()}-jobs"
        
        logger.info(f"Navigating to RemoteOK: {url}")
        
        try:
            await self.navigate(url)
        except Exception as e:
            logger.error(f"RemoteOK navigation failed: {e}")
            return []
            
        await human_delay(3.0, 5.0)
        
        try:
            jobs = await self._scrape_current_page()
            
            if jobs:
                for job in jobs:
                    job["category"] = category
                
                # Save to MongoDB
                if mongo_writer:
                    mongo_writer.upsert_jobs(jobs)
                    logger.success(f"Saved {len(jobs)} jobs to MongoDB")
                
                logger.info(f"Extracted {len(jobs)} jobs from RemoteOK")
            else:
                logger.info("No jobs found on RemoteOK")
                
        except Exception as e:
            logger.error(f"Error scraping RemoteOK: {e}")
            return []
        
        logger.info(f"Total jobs scraped from RemoteOK: {len(jobs)}")
        return jobs
    
    async def _scrape_current_page(self) -> List[Dict]:
        jobs = []
        seen_urls = set()
        try:
            # Full page scroll - RemoteOK uses infinite scroll
            await scroll_page(self.page, steps=15)  # More scrolls to load all content
            
            # Job rows are tr.job
            rows = await self.page.locator("tr.job").all()
            logger.info(f"Found {len(rows)} potential job cards on RemoteOK")

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
                        # Skip duplicates
                        if full_link in seen_urls:
                            continue
                        seen_urls.add(full_link)
                        
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": "Remote",
                            "url": full_link,
                            "source": "RemoteOK"
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping RemoteOK: {e}")
            
        return jobs
