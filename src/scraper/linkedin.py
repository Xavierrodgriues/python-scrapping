from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class LinkedinScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        
        # LinkedIn Guest Search URL with pagination
        # LinkedIn uses start parameter: start=0, start=25, start=50, etc.
        seconds = kwargs.get("days_old", 30) * 86400
        base_url = f"https://www.linkedin.com/jobs/search?keywords={role.replace(' ', '%20')}&location=United%20States&f_TPR=r{seconds}"
        
        all_jobs = []
        current_page = 0
        
        while current_page < max_pages:
            # LinkedIn uses start parameter (25 jobs per page)
            start = current_page * 25
            url = f"{base_url}&start={start}"
            
            logger.info(f"Navigating to LinkedIn page {current_page + 1}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"LinkedIn navigation failed: {e}")
                break
                
            await human_delay(2.0, 4.0)
            
            jobs = await self._scrape_current_page(current_page + 1)
            all_jobs.extend(jobs)
            
            if not jobs:
                logger.info("No jobs found on this page, stopping.")
                break
            
            logger.info(f"Extracted {len(jobs)} jobs from LinkedIn page {current_page + 1}")
            
            current_page += 1
            await human_delay(1.5, 3.0)
        
        logger.info(f"Total jobs scraped from LinkedIn: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        try:
            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Select job cards
            cards = await self.page.locator("ul.jobs-search__results-list li").all()
            
            if not cards or len(cards) == 0:
                cards = await self.page.locator("div.base-card, li.result-card").all()
            
            logger.info(f"Found {len(cards)} potential job cards on LinkedIn page {page_num}")
            
            for card in cards:
                try:
                    title_el = card.locator("h3.base-search-card__title, a.base-card__full-link").first
                    company_el = card.locator("h4.base-search-card__subtitle, a.hidden-nested-link").first
                    location_el = card.locator("span.job-search-card__location").first
                    link_el = card.locator("a.base-card__full-link").first
                    
                    if await title_el.count() == 0:
                        continue
                    
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    loc = await location_el.text_content() if await location_el.count() > 0 else "USA"
                    
                    link = await link_el.get_attribute("href") if await link_el.count() > 0 else None
                    
                    if link and not link.startswith("http"):
                        full_link = f"https://www.linkedin.com{link}"
                    else:
                        full_link = link
                    
                    if title and full_link:
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": loc.strip() if loc else "USA",
                            "url": full_link,
                            "source": "LinkedIn",
                            "page": page_num
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping LinkedIn page {page_num}: {e}")
            
        return jobs
