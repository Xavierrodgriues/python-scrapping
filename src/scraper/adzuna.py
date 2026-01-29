import asyncio
from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class AdzunaScraper(BaseScraper):
    """Scraper for Adzuna USA job listings."""
    
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        
        # Correct Adzuna USA search URL format
        url = f"https://www.adzuna.com/search?q={role.replace(' ', '+')}&w=US"
        
        logger.info(f"Navigating to Adzuna: {url}")
        
        try:
            await self.navigate(url)
        except Exception as e:
            logger.warning(f"Adzuna navigation failed: {e}")
            return []
        
        await self.handle_blockers()
        await human_delay(2.0, 4.0)
        
        all_jobs = []
        current_page = 0
        
        while current_page < max_pages:
            logger.info(f"Scraping Adzuna page {current_page + 1}...")
            
            jobs = await self._scrape_current_page(current_page + 1)
            all_jobs.extend(jobs)
            
            if not jobs:
                logger.info("No jobs found on this page, stopping.")
                break
            
            logger.info(f"Extracted {len(jobs)} jobs from page {current_page + 1}")
            
            current_page += 1
            if current_page >= max_pages:
                break
            
            # Try to go to next page
            has_next = await self._go_to_next_page()
            if not has_next:
                logger.info("No next page found.")
                break
            
            await self.handle_blockers()
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from Adzuna: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        try:
            # Scroll to load all content
            await scroll_page(self.page, steps=10)
            
            # Adzuna uses h2 for job titles with links inside
            title_links = await self.page.locator("h2 a[href*='/land/'], h2 a[href*='/details/']").all()
            
            if not title_links:
                # Try alternative selectors
                title_links = await self.page.locator("a.job_link, a[data-aid]").all()
            
            logger.info(f"Found {len(title_links)} job title links on Adzuna page {page_num}")
            
            for title_link in title_links:
                try:
                    # Get title text
                    title = await title_link.text_content()
                    if not title or len(title.strip()) < 3:
                        continue
                    
                    # Get URL
                    link = await title_link.get_attribute("href")
                    if not link:
                        continue
                    
                    # Ensure full URL
                    if not link.startswith("http"):
                        full_link = f"https://www.adzuna.com{link}"
                    else:
                        full_link = link
                    
                    # Get parent container to find company and location
                    parent = title_link.locator("xpath=ancestor::div[1]")
                    
                    company = "Unknown"
                    loc = "USA"
                    
                    # Try to find company
                    try:
                        parent_div = title_link.locator("xpath=ancestor::div[contains(@class,'result') or position()<=3]").first
                        if await parent_div.count() > 0:
                            company_el = parent_div.locator("a[href*='/company/']").first
                            if await company_el.count() > 0:
                                company = await company_el.text_content()
                    except:
                        pass
                    
                    # Try to find location
                    try:
                        parent_div = title_link.locator("xpath=ancestor::div[position()<=5]").first
                        if await parent_div.count() > 0:
                            loc_el = parent_div.locator("span:has-text(','), .location").first
                            if await loc_el.count() > 0:
                                loc = await loc_el.text_content()
                    except:
                        pass
                    
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip() if company else "Unknown",
                        "location": loc.strip() if loc else "USA",
                        "url": full_link,
                        "source": "Adzuna",
                        "page": page_num
                    })
                    
                except Exception as e:
                    logger.debug(f"Error extracting job: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Adzuna page {page_num}: {e}")
        
        return jobs
    
    async def _go_to_next_page(self) -> bool:
        """Click next page button."""
        try:
            next_selectors = [
                "a[aria-label='Next']",
                "a.next",
                "a[rel='next']",
                "button[aria-label='Next']",
                "a:has-text('Next')",
                "a:has-text('›')",
                "li.next a"
            ]
            
            for sel in next_selectors:
                next_btn = self.page.locator(sel).first
                if await next_btn.count() > 0 and await next_btn.is_visible():
                    logger.info("Clicking Next page on Adzuna...")
                    await next_btn.click()
                    await human_delay(2.0, 4.0)
                    return True
            
            return False
        except Exception as e:
            logger.debug(f"Next page click failed: {e}")
            return False
