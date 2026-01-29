from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class MonsterScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        
        # Monster URL with pagination
        base_url = f"https://www.monster.com/jobs/search?q={role.replace(' ', '+')}&where=United%20States"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            url = f"{base_url}&page={current_page}&so=p.sh"
            
            logger.info(f"Navigating to Monster page {current_page}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"Monster navigation failed: {e}")
                break
                
            await human_delay(3.0, 5.0)
            
            jobs = await self._scrape_current_page(current_page)
            all_jobs.extend(jobs)
            
            if not jobs:
                logger.info("No jobs found on this page, stopping.")
                break
            
            logger.info(f"Extracted {len(jobs)} jobs from Monster page {current_page}")
            
            current_page += 1
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from Monster: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        try:
            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Monster selectors
            cards = await self.page.locator("div[data-component='job-card'], article").all()
            
            if not cards or len(cards) == 0:
                cards = await self.page.locator(".card, div.job-card").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Monster page {page_num}")
            
            for card in cards:
                try:
                    title_el = card.locator("a[data-test-id='svx-job-title'], h3, .job-title").first
                    title = await title_el.text_content() if await title_el.count() > 0 else None
                    
                    if not title or len(title.strip()) < 3:
                        continue
                    
                    company_el = card.locator("span[data-test-id='svx-job-company'], .company-name").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    location_el = card.locator("span[data-test-id='svx-job-location'], .location").first
                    loc = await location_el.text_content() if await location_el.count() > 0 else "USA"
                    
                    url_el = card.locator("a").first
                    link = await url_el.get_attribute("href") if await url_el.count() > 0 else None
                    
                    if link and not link.startswith("http"):
                        full_link = f"https://www.monster.com{link}"
                    else:
                        full_link = link
                    
                    if title and full_link:
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": loc.strip() if loc else "USA",
                            "url": full_link,
                            "source": "Monster",
                            "page": page_num
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Monster page {page_num}: {e}")
            
        return jobs
