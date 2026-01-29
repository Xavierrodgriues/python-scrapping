import asyncio
from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class IndeedScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Indeed URL structure
        days = kwargs.get("days_old", 30)
        max_pages = kwargs.get("max_pages", 1)
        
        url = f"https://www.indeed.com/jobs?q={role.replace(' ', '+')}&l={location.replace(' ', '+')}&fromage={days}"
        
        logger.info(f"Navigating to Indeed: {url}")
        
        try:
            await self.navigate(url)
        except Exception as e:
            logger.warning(f"Indeed navigation timed out: {e}")
            return []
        
        await self.handle_blockers()
        await human_delay(3.0, 5.0)
        
        all_jobs = []
        current_page = 0
        
        while current_page < max_pages:
            logger.info(f"Scraping page {current_page + 1}...")
            
            jobs = await self._scrape_current_page(role, location, current_page + 1)
            all_jobs.extend(jobs)
            
            if not jobs:
                break
                
            current_page += 1
            if current_page >= max_pages:
                break
                
            has_next = await self._go_to_next_page()
            if not has_next:
                logger.info("No next page found.")
                break
                
            await self.handle_blockers()
            await human_delay(3.0, 5.0)
            
        return all_jobs

    async def _scrape_current_page(self, role, location, page_num) -> List[Dict]:
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Wait for job cards
            try:
                await self.page.wait_for_selector("div.job_seen_beacon", timeout=5000)
            except:
                pass
            
            cards = await self.page.locator("div.job_seen_beacon").all()
            if not cards:
                cards = await self.page.locator("td.resultContent").all()
            
            logger.info(f"Found {len(cards)} cards on page {page_num}")
            
            for card in cards:
                try:
                    title_el = card.locator("h2.jobTitle span").first
                    title = await title_el.text_content() if await title_el.count() > 0 else "Unknown Title"
                    
                    company_el = card.locator("[data-testid='company-name']").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown Company"
                    
                    location_el = card.locator("[data-testid='text-location']").first
                    loc = await location_el.text_content() if await location_el.count() > 0 else "Unknown Location"
                    
                    url_el = card.locator("h2.jobTitle a").first
                    link = await url_el.get_attribute("href")
                    full_link = f"https://www.indeed.com{link}" if link and not link.startswith("http") else link
                    
                    if title != "Unknown Title":
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": loc.strip(),
                            "url": full_link,
                            "source": "Indeed",
                            "page": page_num
                        })
                except Exception as e:
                    continue
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}")
            
        return jobs

    async def _go_to_next_page(self) -> bool:
        try:
            # Selectors for Next button
            next_btn = self.page.locator("a[data-testid='pagination-page-next']").first
            if await next_btn.count() == 0:
                 next_btn = self.page.locator("a[aria-label='Next']").first
            
            if await next_btn.count() > 0:
                logger.info("Clicking Next page...")
                await next_btn.click()
                return True
            return False
        except Exception as e:
            logger.warning(f"Error clicking next page: {e}")
            return False
