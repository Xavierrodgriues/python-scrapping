from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class GlassdoorScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        
        days_old = kwargs.get("days_old", 30)
        
        # Glassdoor USA search URL with proper country filter
        encoded_role = role.replace(' ', '%20')
        base_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={encoded_role}&locT=N&locId=1&locKeyword=United%20States&fromAge={days_old}"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            # Glassdoor uses IP parameter for pagination
            url = f"{base_url}&p={current_page}" if current_page > 1 else base_url
            
            logger.info(f"Navigating to Glassdoor USA page {current_page}: {url}")
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"Glassdoor navigation failed: {e}")
                break

            await human_delay(3.0, 6.0)
            
            jobs = await self._scrape_current_page(current_page)
            all_jobs.extend(jobs)
            
            if not jobs:
                logger.info("No jobs found on this page, stopping.")
                break
            
            logger.info(f"Extracted {len(jobs)} jobs from Glassdoor page {current_page}")
            
            current_page += 1
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from Glassdoor: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        try:
            # Check for popup and close if possible
            try:
                close_button = self.page.locator("span.SVGInline.modal_closeIcon, button[aria-label='Close'], button.CloseButton").first
                if await close_button.is_visible(timeout=3000):
                    await close_button.click()
                    await human_delay(1.0, 2.0)
            except:
                pass

            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Select job cards
            cards = await self.page.locator("li[data-test='jobListing'], div.JobCard, article.job-card").all()
            
            if not cards or len(cards) == 0:
                cards = await self.page.locator("div[data-test='job-card'], li.react-job-listing").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Glassdoor page {page_num}")
            
            for card in cards:
                try:
                    title_el = card.locator("a[data-test='job-title'], a.JobCard_jobTitle, h3 a").first
                    title = await title_el.text_content() if await title_el.count() > 0 else None
                    
                    if not title or len(title.strip()) < 3:
                        continue
                    
                    company_el = card.locator("div.employer-name, span.EmployerProfile_companyName, .employer-name").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    location_el = card.locator("div[data-test='emp-location'], span.JobCard_location, .location").first
                    loc = await location_el.text_content() if await location_el.count() > 0 else "USA"
                    
                    url_el = card.locator("a[data-test='job-title'], a.JobCard_jobTitle, a[href*='/job-listing/']").first
                    link = await url_el.get_attribute("href") if await url_el.count() > 0 else None
                    
                    if link and not link.startswith("http"):
                        full_link = f"https://www.glassdoor.com{link}"
                    else:
                        full_link = link

                    if title and full_link:
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": loc.strip() if loc else "USA",
                            "url": full_link,
                            "source": "Glassdoor",
                            "page": page_num
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Glassdoor page {page_num}: {e}")
            
        return jobs
