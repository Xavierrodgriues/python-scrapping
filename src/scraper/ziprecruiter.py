import asyncio
from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class ZipRecruiterScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # ZipRecruiter Search URL
        days = kwargs.get("days_old", 30)
        max_pages = kwargs.get("max_pages", 1)
        
        url = f"https://www.ziprecruiter.com/candidate/search?search={role.replace(' ', '+')}&location={location.replace(' ', '+')}&days={days}"
        logger.info(f"Navigating to ZipRecruiter: {url}")
        
        try:
            await self.navigate(url)
        except Exception as e:
            logger.warning(f"ZipRecruiter navigation timed out or failed: {e}")
            return []

        # Handle capturing popup specifically
        await self.handle_blockers()
        
        # Special check for the "email capture" logic if Escape didn't work
        try:
            content = await self.page.content()
            if "We found" in content and "open positions" in content:
                logger.info("ZipRecruiter email capture detected. Trying aggressive dismissal.")
                await self.page.mouse.click(10, 10)
                await human_delay(1.0, 2.0)
        except:
            pass

        await human_delay(3.0, 5.0)
        
        all_jobs = []
        current_page = 0
        
        while current_page < max_pages:
            logger.info(f"Scraping page {current_page + 1}...")
            
            jobs = await self._scrape_current_page(current_page + 1)
            all_jobs.extend(jobs)
            
            if not jobs:
                break
            
            current_page += 1
            if current_page >= max_pages:
                break
            
            has_next = await self._go_to_next_page()
            if not has_next:
                break
                
            await self.handle_blockers()
            await human_delay(3.0, 5.0)
            
        return all_jobs

    async def _scrape_current_page(self, page_num) -> List[Dict]:
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Expanded Job card selectors
            selectors = [
                 "article.job_result",
                 "div.job_content",
                 "div[class*='job_result']", 
                 "li.job-listing",
                 "article" # fallback to generic article
            ]
            
            cards = []
            for sel in selectors:
                cards = await self.page.locator(sel).all()
                if cards:
                    logger.debug(f"Matched selector: {sel} with {len(cards)} items")
                    break
            
            logger.info(f"Found {len(cards)} potential job cards on ZipRecruiter page {page_num}")

            for card in cards:
                try:
                    title_el = card.locator("h2, h3, .job_title").first
                    company_el = card.locator(".company_name, .company_location, p.org").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link_el = card.locator("a.job_link, a").first
                    link = await link_el.get_attribute("href")
                    
                    # Ensure full URL
                    if link and not link.startswith("http"):
                        full_link = f"https://www.ziprecruiter.com{link}"
                    else:
                        full_link = link
                    
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "USA", 
                        "url": full_link,
                        "source": "ZipRecruiter",
                        "page": page_num
                    })
                except Exception as e:
                    continue
        except Exception as e:
            logger.error(f"Error scraping ZipRecruiter page {page_num}: {e}")
            
        return jobs

    async def _go_to_next_page(self) -> bool:
        try:
            # Next button
            next_btn = self.page.locator("a.next_page, a[aria-label='Next']").first
            if await next_btn.count() > 0:
                logger.info("Clicking Next page on ZipRecruiter...")
                await next_btn.click()
                return True
            return False
        except:
            return False
