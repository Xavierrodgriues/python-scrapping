from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class IndeedScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        days = kwargs.get("days_old", 30)
        
        # Indeed fromage parameter: 1=24h, 3=3days, 7=week, 14=2weeks
        fromage = 30
        if days <= 1:
            fromage = 1
        elif days <= 3:
            fromage = 3
        elif days <= 7:
            fromage = 7
        elif days <= 14:
            fromage = 14
        
        # Indeed uses start parameter for pagination (10 jobs per page)
        base_url = f"https://www.indeed.com/jobs?q={role.replace(' ', '+')}&l=United+States&fromage={fromage}"
        
        all_jobs = []
        current_page = 0
        
        while current_page < max_pages:
            start = current_page * 10
            url = f"{base_url}&start={start}"
            
            logger.info(f"Navigating to Indeed page {current_page + 1}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"Indeed navigation failed: {e}")
                break
            
            await human_delay(3.0, 5.0)
            
            jobs = await self._scrape_current_page(current_page + 1)
            all_jobs.extend(jobs)
            
            if not jobs:
                logger.info("No jobs found on this page, stopping.")
                break
            
            logger.info(f"Extracted {len(jobs)} jobs from Indeed page {current_page + 1}")
            
            current_page += 1
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from Indeed: {len(all_jobs)}")
        return all_jobs

    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        try:
            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Wait for job cards
            try:
                await self.page.wait_for_selector("div.job_seen_beacon, div.jobsearch-ResultsList", timeout=10000)
            except:
                pass
            
            cards = await self.page.locator("div.job_seen_beacon").all()
            
            if not cards or len(cards) == 0:
                cards = await self.page.locator("div.result, li.css-5lfssm").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Indeed page {page_num}")
            
            for card in cards:
                try:
                    title_el = card.locator("h2.jobTitle span[title], a.jcs-JobTitle span").first
                    if await title_el.count() == 0:
                        title_el = card.locator("h2.jobTitle a, h2 a").first
                    
                    company_el = card.locator("span[data-testid='company-name'], span.companyName").first
                    location_el = card.locator("div[data-testid='text-location'], div.companyLocation").first
                    link_el = card.locator("a.jcs-JobTitle, h2.jobTitle a").first
                    
                    title = await title_el.text_content() if await title_el.count() > 0 else None
                    
                    if not title or len(title.strip()) < 3:
                        continue
                    
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    loc = await location_el.text_content() if await location_el.count() > 0 else "USA"
                    
                    link = await link_el.get_attribute("href") if await link_el.count() > 0 else None
                    
                    if link and not link.startswith("http"):
                        full_link = f"https://www.indeed.com{link}"
                    else:
                        full_link = link

                    if title and full_link:
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": loc.strip() if loc else "USA",
                            "url": full_link,
                            "source": "Indeed",
                            "page": page_num
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Indeed page {page_num}: {e}")
            
        return jobs
