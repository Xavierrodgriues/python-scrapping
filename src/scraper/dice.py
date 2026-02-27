from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class DiceScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        
        days_old = kwargs.get("days_old", 30)
        
        # Dice Search URL with pagination
        # Dice uses ?page=1, ?page=2, etc.
        base_url = f"https://www.dice.com/jobs?q={role.replace(' ', '+')}&location=United%20States&filters.postedDate={days_old}"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            url = f"{base_url}&page={current_page}"
            logger.info(f"Navigating to Dice page {current_page}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"Dice navigation failed: {e}")
                break
                
            await human_delay(4.0, 7.0)
            
            jobs = await self._scrape_current_page(current_page)
            all_jobs.extend(jobs)
            
            if not jobs:
                logger.info("No jobs found on this page, stopping.")
                break
            
            logger.info(f"Extracted {len(jobs)} jobs from Dice page {current_page}")
            
            current_page += 1
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from Dice: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        try:
            # Check for blocks
            title = await self.page.title()
            if "Access Denied" in title or "Security" in title:
                logger.warning("Dice blocked access. Skipping.")
                return []
            
            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Job cards are dhi-search-card or similar
            cards = await self.page.locator("dhi-search-card").all()
            
            if not cards or len(cards) == 0:
                # Alternative selectors
                cards = await self.page.locator("a[data-cy='card-title-link'], div.card-header").all()
            
            if not cards or len(cards) == 0:
                # Try finding job title links
                title_links = await self.page.locator("a.card-title-link, a[href*='/job-detail/']").all()
                logger.info(f"Found {len(title_links)} job links on Dice page {page_num}")
                
                for link_el in title_links:
                    try:
                        title = await link_el.text_content()
                        link = await link_el.get_attribute("href")
                        
                        if not title or len(title.strip()) < 3:
                            continue
                        
                        if link and not link.startswith("http"):
                            full_link = f"https://www.dice.com{link}"
                        else:
                            full_link = link
                        
                        jobs.append({
                            "title": title.strip(),
                            "company": "Unknown",
                            "location": "USA",
                            "url": full_link,
                            "source": "Dice",
                            "page": page_num
                        })
                    except:
                        continue
                
                return jobs
            
            logger.info(f"Found {len(cards)} potential job cards on Dice page {page_num}")

            for card in cards:
                try:
                    title_el = card.locator("a.card-title-link, h5 a").first
                    company_el = card.locator("a.card-company-link, span.company-name").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://www.dice.com{link}" if link and not link.startswith("http") else link

                    if title and full_link:
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": "USA",
                            "url": full_link,
                            "source": "Dice",
                            "page": page_num
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Dice page {page_num}: {e}")
            
        return jobs
